"""Run manually at the CircuitPython REPL after Ctrl-C stops code.py.
import diagnostics; diagnostics.run()
No HID or networking. Ctrl-C closes GPIO objects. Copy center/ranges to config.
"""
import time
import board
import analogio
import keypad
import rotaryio
import config

def run():
    resources=[]
    try:
        matrix=keypad.KeyMatrix(tuple(getattr(board,p) for p in config.ROW_PINS),
                               tuple(getattr(board,p) for p in config.COLUMN_PINS),
                               columns_to_anodes=config.COLUMNS_TO_ANODES,
                               interval=.005,debounce_threshold=3)
        resources.append(matrix)
        buttons=keypad.Keys((getattr(board,config.ENCODER_CLICK),getattr(board,config.JOYSTICK_CLICK)),
                            value_when_pressed=False,pull=True,interval=.005,debounce_threshold=3)
        resources.append(buttons)
        encoder=rotaryio.IncrementalEncoder(getattr(board,config.ENCODER_A),getattr(board,config.ENCODER_B),
                                            divisor=config.ENCODER_DIVISOR)
        resources.append(encoder)
        x=analogio.AnalogIn(getattr(board,config.JOYSTICK_X));resources.append(x)
        y=analogio.AnalogIn(getattr(board,config.JOYSTICK_Y));resources.append(y)
        print('No HID output. Move axes to ends, center, and note raw ADC values.')
        while True:
            for name,scanner in (('matrix',matrix),('click',buttons)):
                while True:
                    event=scanner.events.get()
                    if event is None:break
                    print(name,event.key_number,'pressed' if event.pressed else 'released')
            print('X',x.value,'Y',y.value,'encoder',encoder.position)
            time.sleep(.1)
    finally:
        for resource in reversed(resources):resource.deinit()
