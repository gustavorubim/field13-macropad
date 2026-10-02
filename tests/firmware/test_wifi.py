import pathlib
import sys
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'firmware'))
sys.path.insert(0,str(ROOT/'firmware'/'companion'))
from macropad import wire
from wifi_companion import Receiver, WindowsInput, allowed_map

KEY=b'0123456789abcdef0123456789abcdef'
BOOT=b'11111111111111111111111111111111'
SESSION=b'22222222222222222222222222222222'
REPORT=bytes([0,0,104,0,0,0,0,0])

class WireTests(unittest.TestCase):
    def test_hmac_rfc4231(self):
        self.assertEqual(wire.mac(b'\x0b'*20,b'Hi There'),
            b'b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7')
    def test_signed_hello_challenge(self):
        self.assertEqual(wire.parse_hello(KEY,wire.hello(KEY,BOOT)),BOOT)
        packet=wire.challenge(KEY,BOOT,SESSION)
        self.assertEqual(wire.parse_challenge(KEY,BOOT,packet),SESSION)
        with self.assertRaises(ValueError):wire.parse_challenge(KEY,SESSION,packet)
    def test_report_roundtrip(self):
        p=wire.pack(KEY,SESSION,1,REPORT,{'buttons':0,'wheel':1})
        self.assertEqual(wire.unpack(KEY,SESSION,-1,p),(1,REPORT,{'buttons':0,'wheel':1}))
    def test_tamper_wrong_key_wrong_nonce_replay(self):
        packet=wire.pack(KEY,SESSION,2,REPORT)
        for key,nonce,last,value in ((b'wrong',SESSION,0,packet),(KEY,BOOT,0,packet),
                                     (KEY,SESSION,2,packet),(KEY,SESSION,3,packet),
                                     (KEY,SESSION,0,packet[:-1]+b'z')):
            with self.assertRaises(ValueError):wire.unpack(key,nonce,last,value)
    def test_bounded_malformed_packet(self):
        for value in (b'',b'x'*1537,b'not json'):
            with self.assertRaises(ValueError):wire.unpack(KEY,SESSION,0,value)

class ReceiverTests(unittest.TestCase):
    def setUp(self):
        self.calls=[];self.counter=2
        def nonce():
            self.counter+=1
            return ('%032x'%self.counter).encode()
        self.r=Receiver(KEY,lambda report,event:self.calls.append((report,event)),nonce_factory=nonce)
        response=self.r.hello(wire.hello(KEY,BOOT))
        self.session=wire.parse_challenge(KEY,BOOT,response)
        self.calls.clear()
    def send(self,event=None,report=REPORT,seq=1,now=10):
        self.r.accept(wire.pack(KEY,self.session,seq,report,event),now)
    def test_accepted_snapshot_and_timeout_release_rotate(self):
        self.send();self.assertEqual(self.r.report,REPORT)
        self.r.tick(10.4);self.assertEqual(self.r.report,REPORT)
        self.r.tick(10.6);self.assertEqual(self.r.report,bytes(8))
        self.assertNotEqual(self.r.session,self.session)
        self.assertEqual(self.calls[-1],(bytes(8),{'buttons':0}))
        with self.assertRaises(ValueError):self.send(seq=2,now=11)
    def test_unconfigured_key_and_bad_event_rejected_without_sequence_change(self):
        for event,report in (({'command':'approve'},REPORT),({'wheel':128},REPORT),
                             ({'buttons':True},REPORT),({'buttons':1},REPORT),
                             ({'media':'ARBITRARY'},REPORT),({'media':[]},REPORT),
                             ({'x':1},REPORT),({},bytes([0,0,100,0,0,0,0,0])),
                             ({},bytes([0,0,104,104,0,0,0,0]))):
            with self.assertRaises(ValueError):self.send(event,report)
            self.assertEqual(self.r.sequence,-1)
        self.assertFalse(self.calls)
    def test_media_wheel_and_ordering(self):
        self.send({'media':'MUTE'},seq=1)
        self.send({'wheel':-1},seq=2)
        with self.assertRaises(ValueError):self.send(seq=1)
        self.assertEqual(len(self.calls),2)
    def test_hello_does_not_refresh_report_timeout(self):
        self.send();self.r.hello(wire.hello(KEY,BOOT));self.r.tick(11)
        self.assertEqual(self.r.report,bytes(8))
    def test_wrong_psk_hello_does_not_release(self):
        self.send()
        with self.assertRaises(ValueError):self.r.hello(wire.hello(b'other',BOOT))
        self.assertEqual(self.r.report,REPORT)
    def test_all_configured_usages_have_windows_mappings(self):
        mods,usages,media,buttons=allowed_map()
        for usage in usages-{0}:self.assertIsNotNone(WindowsInput.vk(usage))

if __name__=='__main__': unittest.main()
