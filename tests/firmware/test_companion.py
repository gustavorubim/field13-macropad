import os
import pathlib
import pty
import socket
import sys
import tempfile
import unittest
from unittest import mock
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'firmware'/'companion'))
import microbridge_companion as mb

def frame(color='#804020',brightness=50,paused=False):
    return {'keys':[{'color':color,'focused':False,'session_id':str(i),'state':'working'}
                    for i in range(6)],'brightness':brightness,'paused':paused}

class ProtocolTests(unittest.TestCase):
    def test_decoder_retains_every_batched_frame(self):
        p=mb.NDJSON(128); messages=[{'v':1,'type':'activate','index':i} for i in range(6)]
        data=b''.join(mb.encode(x) for x in messages)
        self.assertEqual(p.feed(data[:11]),[])
        self.assertEqual(p.feed(data[11:]),messages)
    def test_decoder_recovers_from_bad_large_and_nonobjects(self):
        p=mb.NDJSON(32)
        self.assertEqual(p.feed(b'x'*500),[])
        self.assertEqual(p.feed(b'\nNaN\n[]\n\xff\n'+mb.encode({'ok':1})),[{'ok':1}])
        self.assertEqual(len(p.buffer),0)
    def test_led_scale_pause_and_invalid(self):
        self.assertEqual(mb.led_colors(frame()),((64,32,16),)*6)
        self.assertEqual(mb.led_colors(frame(paused=True)),mb.BLACK)
        self.assertEqual(mb.led_colors(frame(color=None)),mb.BLACK)
        for bad in ({},frame(color='red'),frame(brightness=True),frame(paused=1)):
            self.assertIsNone(mb.led_colors(bad))
    def test_only_exact_bounded_activation(self):
        for i in range(6): self.assertEqual(mb.activation_index({'v':1,'type':'activate','index':i}),i)
        for bad in ({'v':1,'type':'approve','index':0}, {'v':1,'type':'activate','index':6},
                    {'v':1,'type':'activate','index':True}, {'v':True,'type':'activate','index':0},
                    {'v':1,'type':'activate','index':0,'command':'approve'}):
            self.assertIsNone(mb.activation_index(bad))

class RelayIntegration(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=os.path.join(self.temp.name,'daemon.sock')
        try:
            self.server=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        except PermissionError:
            self.temp.cleanup()
            self.skipTest('Host environment denies Unix sockets; run on a normal macOS/Linux host')
        self.server.bind(self.path);self.server.listen();self.server.setblocking(False)
        self.master,self.slave=pty.openpty();os.set_blocking(self.master,False)
        self.now=1.0
        self.relay=mb.Companion(os.ttyname(self.slave),self.path,clock=lambda:self.now)
        self.connection=None;self.daemon_parser=mb.NDJSON(262144)
        self.serial_parser=mb.NDJSON(2048);self.commands=[];self.leds=[]
    def tearDown(self):
        self.relay.close()
        if self.connection:self.connection.close()
        self.server.close();os.close(self.master);os.close(self.slave);self.temp.cleanup()
    def pump(self,count=20):
        for _ in range(count):
            self.relay.step(0);self.now+=0.01
            if self.connection is None:
                try:self.connection,_=self.server.accept();self.connection.setblocking(False)
                except BlockingIOError:pass
            if self.connection:
                try:
                    data=self.connection.recv(65536)
                    if data:self.commands.extend(self.daemon_parser.feed(data))
                except BlockingIOError:pass
            try:self.leds.extend(self.serial_parser.feed(os.read(self.master,65536)))
            except BlockingIOError:pass
    def ready(self):
        self.pump()
        self.assertEqual(self.commands[:2],[mb.HELLO,mb.SUBSCRIBE])
        self.connection.sendall(mb.encode({'type':'snapshot','snapshot':{'agent_key_led_frame':frame()}}))
        self.pump();self.assertTrue(self.relay.ready)
    def test_handshake_six_batch_activations_update_and_disconnect(self):
        self.ready()
        self.assertEqual(self.leds[-1]['colors'],[[64,32,16]]*6)
        data=b''.join(mb.encode({'v':1,'type':'activate','index':i}) for i in range(6))
        os.write(self.master,data[:13]);self.pump(2);os.write(self.master,data[13:]);self.pump(150)
        activations=[m for m in self.commands if m['type']=='activate_agent_key']
        self.assertEqual(activations,[{'type':'activate_agent_key','index':i,'open':True} for i in range(6)])
        self.connection.sendall(mb.encode({'type':'event','event':{'kind':'agent_keys_changed','led_frame':frame('#00ff00',100)}}))
        self.pump();self.assertEqual(self.leds[-1]['colors'],[[0,255,0]]*6)
        self.connection.close();self.connection=None;self.pump(10)
        self.assertFalse(self.relay.ready);self.assertEqual(self.leds[-1]['colors'],[[0,0,0]]*6)
    def test_offline_and_invalid_activations_do_not_replay(self):
        self.pump()
        os.write(self.master,mb.encode({'v':1,'type':'activate','index':2}));self.pump()
        self.connection.sendall(mb.encode({'type':'snapshot','snapshot':{'agent_key_led_frame':frame()}}))
        self.pump()
        os.write(self.master,mb.encode({'v':1,'type':'approve','index':0}));self.pump()
        self.assertFalse([m for m in self.commands if m['type']=='activate_agent_key'])
    def test_stale_daemon_goes_dark_and_drops_pending(self):
        self.ready();self.relay._handle_serial({'v':1,'type':'activate','index':0},self.now)
        self.now+=7;self.pump(5)
        self.assertFalse(self.relay.ready);self.assertFalse(self.relay.activations)
        self.assertEqual(self.leds[-1]['colors'],[[0,0,0]]*6)
    def test_partial_expired_activation_closes_stream(self):
        self.ready()
        self.relay.daemon_output.append([b'{"type":"activate_agent_key"}\n',1,self.now-1])
        self.relay._write_daemon(self.now)
        self.assertIsNone(self.relay.daemon)
    def test_serial_open_failure_clears_fd(self):
        with mock.patch.object(self.relay,'_interest',side_effect=OSError('simulated')):
            self.relay._open_serial(self.now)
        self.assertIsNone(self.relay.serial_fd)

class MemorySocket:
    def __init__(self): self.input=b'';self.output=b'';self.closed=False
    def send(self,data): self.output+=data;return len(data)
    def recv(self,size):
        data,self.input=self.input[:size],self.input[size:]
        return data
    def close(self): self.closed=True

class RelayMockTests(unittest.TestCase):
    def setUp(self):
        self.relay=mb.Companion('/not-opened','/not-opened',clock=lambda:1.0)
        self.relay.selector.close();self.relay.selector=mock.MagicMock()
        self.sock=MemorySocket();self.relay.daemon=self.sock
        self.relay._daemon_connected(1.0);self.relay._write_daemon(1.0)
        self.assertEqual(mb.NDJSON(1024).feed(self.sock.output),[mb.HELLO,mb.SUBSCRIBE])
    def tearDown(self):
        self.relay.serial_fd=None;self.relay.close()
    def make_ready(self):
        self.relay._handle_daemon({'type':'snapshot','snapshot':{'agent_key_led_frame':frame()}},1.0)
        self.assertTrue(self.relay.ready)
    def test_complete_batched_serial_read_preserves_six_actions(self):
        self.make_ready();self.relay.serial_fd=42
        packet=b''.join(mb.encode({'v':1,'type':'activate','index':i}) for i in range(6))
        with mock.patch.object(mb.os,'read',return_value=packet):self.relay._read_serial(1.0)
        for i in range(6):
            now=1+i*0.21;self.relay._pump_activations(now);self.relay._write_daemon(now)
        commands=mb.NDJSON(4096).feed(self.sock.output)[2:]
        self.assertEqual(commands,[{'type':'activate_agent_key','index':i,'open':True} for i in range(6)])
    def test_offline_commands_and_expired_queue_are_dropped(self):
        self.relay._handle_serial({'v':1,'type':'activate','index':1},1)
        self.assertFalse(self.relay.activations)
        self.make_ready();self.relay._handle_serial({'v':1,'type':'activate','index':1},1)
        self.relay._pump_activations(4);self.assertFalse(self.relay.activations)
        self.assertEqual(len(mb.NDJSON(4096).feed(self.sock.output)),2)
    def test_partial_stale_command_closes_socket(self):
        self.make_ready();self.relay.daemon_output.append([b'partial',1,0.0])
        self.relay._write_daemon(1);self.assertTrue(self.sock.closed)
        self.assertFalse(self.relay.ready);self.assertEqual(self.relay.colors,mb.BLACK)
    def test_snapshot_then_event_batch_updates_latest_colors(self):
        one={'type':'snapshot','snapshot':{'agent_key_led_frame':frame()}}
        two={'type':'event','event':{'kind':'agent_keys_changed','led_frame':frame('#ff0000',100)}}
        self.sock.input=mb.encode(one)+mb.encode(two)
        self.relay._read_daemon(1.0);self.assertEqual(self.relay.colors,((255,0,0),)*6)
    def test_unknown_led_schema_fails_dark(self):
        self.make_ready();self.relay._handle_daemon({'type':'snapshot','snapshot':{}},2)
        self.assertTrue(self.sock.closed);self.assertEqual(self.relay.colors,mb.BLACK)
    def test_partial_serial_output_retains_latest_complete_frame(self):
        self.relay.serial_fd=42;self.relay._queue_leds(((1,2,3),)*6)
        with mock.patch.object(mb.os,'write',return_value=5):self.relay._write_serial(1)
        first=self.relay.serial_output;self.relay._queue_leds(((4,5,6),)*6)
        self.relay._queue_leds(((7,8,9),)*6)
        self.assertEqual(self.relay.serial_output,first)
        self.assertEqual(mb.NDJSON(1024).feed(self.relay.serial_pending)[0]['colors'],[[7,8,9]]*6)

if __name__=='__main__': unittest.main()
