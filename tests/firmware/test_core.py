import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'firmware'))
from macropad.actions import keys, tap, momentary, toggle, consumer, mouse_button, agent, NONE
from macropad.engine import Engine
from macropad.inputs import Debouncer, Axis, EncoderDelta, ArmGuard
from macropad.framing import Lines, encode, led_colors
import config

class FakeSink:
    def __init__(self):
        self.events, self.held, self.mouse_held = [], set(), set()
    def key_down(self, value):
        self.events.append(('down', value)); self.held.add(value)
    def key_up(self, value):
        self.events.append(('up', value)); self.held.discard(value)
    def tap_delay(self): pass
    def consumer(self, value): self.events.append(('media', value))
    def wheel(self, value): self.events.append(('wheel', value))
    def mouse_down(self, value): self.mouse_held.add(value)
    def mouse_up(self, value): self.mouse_held.discard(value)
    def agent(self, value): self.events.append(('agent', value))
    def release_all(self):
        self.held.clear(); self.mouse_held.clear(); self.events.append(('reset',))

class EngineTests(unittest.TestCase):
    def setUp(self):
        self.sink = FakeSink()
        self.layers = {0: {'A': keys('CTRL', 'A'), 'B': keys('CTRL', 'B'),
                          'FN': momentary(1), 'FN2': momentary(2), 'T': toggle(1),
                          'M': mouse_button(1), 'P': tap('CTRL', 'C')},
                       1: {'A': keys('ALT', 'X'), 'FN2': momentary(2)},
                       2: {'A': keys('SHIFT', 'Y')}}
        self.engine = Engine(self.layers, self.sink)
    def test_release_uses_press_layer(self):
        self.engine.press('A'); self.engine.press('FN'); self.engine.release('A')
        self.assertEqual(self.sink.held, set())
        self.engine.press('A'); self.engine.release('FN'); self.engine.release('A')
        self.assertEqual(self.sink.held, set())
    def test_shared_modifiers_reference_counted(self):
        self.engine.press('A'); self.engine.press('B'); self.engine.release('A')
        self.assertEqual(self.sink.held, {'CTRL', 'B'})
        self.engine.release('B'); self.assertFalse(self.sink.held)
        self.assertEqual(self.sink.events.count(('down','CTRL')), 1)
    def test_duplicate_press_and_release(self):
        self.engine.press('A'); self.engine.press('A'); self.engine.release('A')
        self.engine.release('A'); self.assertFalse(self.sink.held)
        self.assertEqual(self.sink.events.count(('down','A')),1)
    def test_transparent_falls_through(self):
        self.engine.press('FN'); self.engine.press('B')
        self.assertEqual(self.sink.held, {'CTRL', 'B'})
    def test_nested_layers_and_toggle(self):
        self.engine.pulse('T'); self.assertEqual(self.engine.layer_order(), [1,0])
        self.engine.press('FN2'); self.assertEqual(self.engine.layer_order(), [2,1,0])
        self.engine.release('FN2'); self.engine.pulse('T')
        self.assertEqual(self.engine.layer_order(), [0])
    def test_tap_preserves_other_modifier_owner(self):
        self.engine.press('A'); self.engine.pulse('P')
        self.assertEqual(self.sink.held, {'CTRL','A'})
        self.assertNotIn(('up','CTRL'), self.sink.events)
    def test_overlapping_mouse_button_masks_reference_counted(self):
        e=Engine({0:{'A':mouse_button(3),'B':mouse_button(1)}},self.sink)
        e.press('A'); e.press('B'); e.release('A')
        self.assertEqual(self.sink.mouse_held,{1})
        e.release('B'); self.assertFalse(self.sink.mouse_held)
    def test_reset_releases_keyboard_mouse_layers(self):
        self.engine.press('M'); self.engine.press('A'); self.engine.press('FN')
        self.engine.release_all()
        self.assertFalse(self.sink.held); self.assertFalse(self.sink.mouse_held)
        self.assertFalse(self.engine.active); self.assertEqual(self.engine.layer_order(), [0])
    def test_agent_index_bounded(self):
        for bad in (-1,6,True,'0'):
            with self.assertRaises(ValueError): agent(bad)
        self.assertEqual(agent(5), ('agent',5))
    def test_duplicate_keynames_not_double_referenced(self):
        e=Engine({0:{'A':keys('CTRL','CTRL','A')}},self.sink)
        e.press('A'); e.release('A'); self.assertFalse(e.key_refs)
    def test_default_layout_has_thirteen_positions(self):
        self.assertEqual(set(config.MATRIX_TO_KEY), {1,2,4,5,6,7,8,9,10,11,12,13,14})
        self.assertEqual(len(config.MATRIX_TO_KEY),13)
        self.assertTrue(config.COLUMNS_TO_ANODES)

class InputTests(unittest.TestCase):
    def test_debounce_press_and_release(self):
        d=Debouncer(0.015)
        self.assertIsNone(d.update(True,0))
        self.assertIsNone(d.update(False,0.005))
        self.assertIsNone(d.update(True,0.010))
        self.assertIs(d.update(True,0.026),True)
        self.assertIsNone(d.update(True,0.1))
        self.assertIsNone(d.update(False,0.2))
        self.assertIs(d.update(False,0.22),False)
    def test_axis_hysteresis_and_direct_reversal(self):
        a=Axis(center=50,minimum=0,maximum=100)
        self.assertEqual(a.update(66),0)
        self.assertEqual(a.update(70),1)
        self.assertEqual(a.update(64),1)
        self.assertEqual(a.update(60),0)
        self.assertEqual(a.update(20),-1)
        self.assertEqual(a.update(90),1)
    def test_inversion_clamping_and_calibration(self):
        a=Axis(center=100,minimum=20,maximum=200,inverted=True)
        self.assertEqual(a.normalize(-30),1)
        self.assertEqual(a.normalize(999),-1)
        for kwargs in ({'center':0}, {'leave':0.8}, {'minimum':40000}):
            with self.assertRaises(ValueError): Axis(**kwargs)
    def test_encoder_retains_batch(self):
        e=EncoderDelta(0); e.update(4)
        self.assertEqual([e.pop() for _ in range(5)],[1,1,1,1,0])
        e.update(2); self.assertEqual([e.pop(),e.pop()],[-1,-1])
    def test_encoder_inversion_and_overflow(self):
        e=EncoderDelta(10,inverted=True,max_pending=5); e.update(12)
        self.assertEqual(e.pop(),-1)
        e.update(100); self.assertTrue(e.overflowed); self.assertEqual(e.pop(),0)
        e.reset(10); self.assertFalse(e.overflowed)
    def test_arm_requires_released_keys_center_connected(self):
        g=ArmGuard(0.1); g.event('K',True)
        self.assertFalse(g.update(0)); self.assertFalse(g.update(1))
        g.event('K',False); self.assertFalse(g.update(2,neutral=False))
        self.assertFalse(g.update(3)); self.assertTrue(g.update(3.2))
        self.assertFalse(g.update(4,connected=False)); self.assertFalse(g.update(5))
        self.assertTrue(g.update(5.2))

class FramingTests(unittest.TestCase):
    def test_fragments_batches_and_invalid_records(self):
        parser=Lines(); a={'v':1,'type':'activate','index':0}; b={'v':1,'type':'activate','index':1}
        data=encode(a)+b'bad\n'+encode(b)
        self.assertEqual(parser.feed(data[:5]),[])
        self.assertEqual(parser.feed(data[5:]),[a,b])
    def test_oversized_then_valid_recovers(self):
        p=Lines(32); self.assertEqual(p.feed(b'x'*50),[])
        self.assertLessEqual(len(p.buffer),32)
        self.assertEqual(p.feed(b'\n'+encode({'ok':True})),[{'ok':True}])
    def test_led_schema_rejects_bad_input(self):
        good={'v':1,'type':'leds','colors':[[1,2,3]]*6}
        self.assertEqual(led_colors(good),[(1,2,3)]*6)
        for delta in ({'v':True}, {'type':'approve'}, {'colors':[[1,2,3]]*5},
                      {'colors':[[True,0,0]]*6}, {'colors':[[256,0,0]]*6}):
            self.assertIsNone(led_colors(dict(good,**delta)))

if __name__ == '__main__': unittest.main()
