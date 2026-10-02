#!/usr/bin/env python3
"""Opt-in authenticated Wi-Fi keyboard/mouse receiver. Default: dry-run.
Windows input injection needs explicit --enable-input. No Microbridge actions.
"""
import argparse
import os
import pathlib
import secrets
import socket
import sys
import time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from macropad.wire import parse_hello, challenge, unpack, MAX_PACKET
from macropad.hid_codes import CODES
import config

ZERO = bytes(8)
MEDIA_VK = {'MUTE':0xAD,'VOLUME_DECREMENT':0xAE,'VOLUME_INCREMENT':0xAF,
            'PLAY_PAUSE':0xB3,'SCAN_NEXT_TRACK':0xB0,'SCAN_PREVIOUS_TRACK':0xB1,'STOP':0xB2}

def allowed_map():
    modifiers, usages, media, buttons = 0, {0}, set(), 0
    for layer in config.LAYERS.values():
        for action in layer.values():
            if action[0] in ('keys','tap'):
                for name in action[1]:
                    code = CODES[name]
                    if code >= 224:
                        modifiers |= 1 << (code - 224)
                    else:
                        usages.add(code)
            elif action[0] == 'consumer':
                if action[1] not in MEDIA_VK:
                    raise ValueError('Wireless media action needs an explicit Windows mapping')
                media.add(action[1])
            elif action[0] == 'mouse_button':
                buttons |= action[1]
    return modifiers, usages, media, buttons

class Receiver:
    def __init__(self, key, sink, nonce=None, nonce_factory=None):
        if len(key) < 32:
            raise ValueError('Use a private random 32+ character PSK')
        self.key, self.sink = key, sink
        self.nonce_factory = nonce_factory or (lambda: secrets.token_hex(16).encode())
        self.session = nonce or self.nonce_factory()
        self.boot, self.sequence, self.last = None, -1, None
        self.report, self.buttons = ZERO, 0
        self.mods, self.usages, self.media, self.allowed_buttons = allowed_map()

    def hello(self, packet):
        boot = parse_hello(self.key, packet)
        if boot != self.boot:
            self.close()
            self.boot, self.session, self.sequence = boot, self.nonce_factory(), -1
            self.last = None
        return challenge(self.key, boot, self.session)

    def accept(self, packet, now):
        if self.boot is None:
            raise ValueError('Handshake required')
        sequence, report, event = unpack(self.key, self.session, self.sequence, packet)
        if report[0] & ~self.mods or any(key not in self.usages for key in report[2:]):
            raise ValueError('Key outside configured allowlist')
        nonzero = [key for key in report[2:] if key]
        if len(set(nonzero)) != len(nonzero):
            raise ValueError('Duplicate key usages')
        if set(event) - {'buttons','media','x','y','wheel'}:
            raise ValueError('Unknown event')
        buttons = event.get('buttons', 0)
        if type(buttons) is not int or not 0 <= buttons <= 7 or buttons & ~self.allowed_buttons:
            raise ValueError('Mouse buttons outside configured allowlist')
        for axis in ('x','y','wheel'):
            if type(event.get(axis,0)) is not int or not -127 <= event.get(axis,0) <= 127:
                raise ValueError('Mouse delta')
        if config.JOYSTICK_MODE != 'mouse' and (event.get('x',0) or event.get('y',0)):
            raise ValueError('Mouse mode not enabled in config')
        if 'media' in event and (not isinstance(event['media'],str) or event['media'] not in self.media):
            raise ValueError('Media outside configured allowlist')
        # Validate everything before advancing replay state or invoking the sink.
        self.sink(report, event)
        self.sequence, self.last = sequence, now
        self.report, self.buttons = report, buttons

    def tick(self, now):
        if self.last is not None and now - self.last > 0.5:
            self.close()
            # Fresh challenge forces a release/re-arm instead of replaying held input.
            self.session, self.sequence, self.last = self.nonce_factory(), -1, None

    def close(self):
        if hasattr(self.sink,'release_all'):
            self.sink.release_all()
        else:
            self.sink(ZERO, {'buttons':0})
        self.report, self.buttons = ZERO, 0

class WindowsInput:
    def __init__(self):
        if sys.platform != 'win32':
            raise RuntimeError('--enable-input is implemented for Windows only')
        import ctypes
        self.ctypes, self.user = ctypes, ctypes.WinDLL('user32', use_last_error=True)
        class Keyboard(ctypes.Structure):
            _fields_=[('wVk',ctypes.c_ushort),('wScan',ctypes.c_ushort),
                      ('dwFlags',ctypes.c_ulong),('time',ctypes.c_ulong),
                      ('dwExtraInfo',ctypes.c_size_t)]
        class Mouse(ctypes.Structure):
            _fields_=[('dx',ctypes.c_long),('dy',ctypes.c_long),
                      ('mouseData',ctypes.c_ulong),('dwFlags',ctypes.c_ulong),
                      ('time',ctypes.c_ulong),('dwExtraInfo',ctypes.c_size_t)]
        class Payload(ctypes.Union):
            _fields_=[('ki',Keyboard),('mi',Mouse)]
        class Input(ctypes.Structure):
            _fields_=[('type',ctypes.c_ulong),('u',Payload)]
        self.Keyboard,self.Mouse,self.Payload,self.Input=Keyboard,Mouse,Payload,Input
        self.user.SendInput.argtypes=[ctypes.c_uint,ctypes.POINTER(Input),ctypes.c_int]
        self.user.SendInput.restype=ctypes.c_uint
        self.held, self.buttons = set(), 0

    @staticmethod
    def vk(code):
        if 4 <= code <= 29: return 65 + code - 4
        if 30 <= code <= 38: return 49 + code - 30
        if code == 39: return 48
        if 58 <= code <= 69: return 112 + code - 58
        if 104 <= code <= 115: return 124 + code - 104
        return {40:13,41:27,42:8,43:9,44:32,45:0xBD,46:0xBB,47:0xDB,
                48:0xDD,49:0xDC,51:0xBA,52:0xDE,53:0xC0,54:0xBC,
                55:0xBE,56:0xBF,57:0x14,70:0x2C,71:0x91,72:0x13,
                73:0x2D,74:0x24,75:0x21,76:0x2E,77:0x23,78:0x22,
                79:0x27,80:0x25,81:0x28,82:0x26}.get(code)

    def _emit(self, event):
        if self.user.SendInput(1,self.ctypes.byref(event),self.ctypes.sizeof(event)) != 1:
            raise OSError('Windows rejected input; elevation/UIPI may block target')

    def _key(self, vk, up):
        flags = 2 if up else 0
        if vk in (0xA3,0xA5,0x5B,0x5C,0x21,0x22,0x23,0x24,0x25,0x26,0x27,0x28,0x2D,0x2E):
            flags |= 1  # KEYEVENTF_EXTENDEDKEY
        self._emit(self.Input(type=1,u=self.Payload(ki=self.Keyboard(vk,0,flags,0,0))))

    def _mouse(self, flags, x=0, y=0, data=0):
        self._emit(self.Input(type=0,u=self.Payload(mi=self.Mouse(x,y,data & 0xffffffff,flags,0,0))))

    def release_all(self):
        # Best effort on EVERY owned key/button even if Windows rejects one.
        failed=False
        for key in tuple(self.held):
            try:
                self._key(key,True); self.held.discard(key)
            except OSError:
                failed=True
        for mask,up in ((1,4),(2,16),(4,64)):
            if self.buttons & mask:
                try:
                    self._mouse(up); self.buttons &= ~mask
                except OSError:
                    failed=True
        if failed:
            print('WARNING: Windows rejected one or more release events',file=sys.stderr)

    def __call__(self, report, event):
        modifiers=(0xA2,0xA0,0xA4,0x5B,0xA3,0xA1,0xA5,0x5C)
        target={self.vk(key) for key in report[2:] if key}
        target |= {modifiers[i] for i in range(8) if report[0] & (1 << i)}
        if None in target: raise ValueError('HID usage lacks a Windows VK mapping')
        # Release ordinary keys before modifiers; press modifiers before keys.
        for key in sorted(self.held-target,key=lambda x:(x in modifiers,x)):
            self._key(key,True); self.held.discard(key)
        for key in sorted(target-self.held,key=lambda x:(x not in modifiers,x)):
            self._key(key,False); self.held.add(key)
        buttons=event.get('buttons',0)
        for mask,down,up in ((1,2,4),(2,8,16),(4,32,64)):
            if bool(buttons & mask) != bool(self.buttons & mask):
                self._mouse(down if buttons & mask else up)
                self.buttons = (self.buttons | mask) if buttons & mask else (self.buttons & ~mask)
        x,y,wheel=event.get('x',0),event.get('y',0),event.get('wheel',0)
        if x or y: self._mouse(1,x,y)
        if wheel: self._mouse(0x0800,data=wheel*120)
        if 'media' in event:
            vk=MEDIA_VK[event['media']]
            self._key(vk,False)
            try: pass
            finally: self._key(vk,True)

class DryRun:
    def __init__(self): self.last = None
    def __call__(self, report, event):
        value=(report,event)
        if value != self.last:
            print('DRY RUN',report.hex(),event)
            self.last=value

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bind',required=True,help='Exact host LAN IPv4 address; no wildcard')
    p.add_argument('--device',required=True,help='Exact Pico IPv4; use a DHCP reservation')
    p.add_argument('--port',type=int,default=41413)
    p.add_argument('--enable-input',action='store_true',help='Enable Windows SendInput (default: dry-run)')
    args=p.parse_args(argv)
    for value in (args.bind,args.device):
        try: socket.inet_pton(socket.AF_INET,value)
        except OSError: p.error('Use literal IPv4 addresses')
        if value in ('0.0.0.0','255.255.255.255'): p.error('Wildcard/broadcast not allowed')
    if not 1 <= args.port <= 65535: p.error('Invalid port')
    secret=os.environ.get('ARC13_PSK','')
    if len(secret)<32 or secret.startswith('REPLACE_'): p.error('Set private random ARC13_PSK (32+ characters)')
    sink=WindowsInput() if args.enable_input else DryRun()
    receiver=Receiver(secret.encode(),sink)
    sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sock.bind((args.bind,args.port)); sock.settimeout(0.05)
    print('Wi-Fi companion:', 'WINDOWS INPUT ENABLED' if args.enable_input else 'DRY RUN')
    try:
        while True:
            try:
                packet,address=sock.recvfrom(MAX_PACKET+1)
                try:
                    if address[0] != args.device:
                        raise ValueError('Unpaired IP')
                    if packet.startswith(b'ARC13/2H|'):
                        sock.sendto(receiver.hello(packet),address)
                    else:
                        receiver.accept(packet,time.monotonic())
                except (ValueError,TypeError,KeyError,UnicodeError):
                    pass
            except socket.timeout: pass
            receiver.tick(time.monotonic())
    except KeyboardInterrupt:
        pass
    finally:
        try: receiver.close()
        finally: sock.close()
    return 0

if __name__=='__main__': raise SystemExit(main())
