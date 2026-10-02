"""USB HID Keyboard/Keypad usage IDs used by the supplied keymap.
Names match adafruit_hid.keycode.Keycode. Extend explicitly for a custom map.
"""
CODES = {chr(65 + i): 4 + i for i in range(26)}
CODES.update({'ONE':30, 'TWO':31, 'THREE':32, 'FOUR':33, 'FIVE':34,
              'SIX':35, 'SEVEN':36, 'EIGHT':37, 'NINE':38, 'ZERO':39,
              'ENTER':40, 'ESCAPE':41, 'BACKSPACE':42, 'TAB':43, 'SPACE':44,
              'MINUS':45, 'EQUALS':46, 'LEFT_BRACKET':47, 'RIGHT_BRACKET':48,
              'BACKSLASH':49, 'SEMICOLON':51, 'QUOTE':52, 'GRAVE_ACCENT':53,
              'COMMA':54, 'PERIOD':55, 'FORWARD_SLASH':56, 'CAPS_LOCK':57,
              'PRINT_SCREEN':70, 'SCROLL_LOCK':71, 'PAUSE':72, 'INSERT':73,
              'HOME':74, 'PAGE_UP':75, 'DELETE':76, 'END':77, 'PAGE_DOWN':78,
              'RIGHT_ARROW':79, 'LEFT_ARROW':80, 'DOWN_ARROW':81, 'UP_ARROW':82,
              'LEFT_CONTROL':224, 'LEFT_SHIFT':225, 'LEFT_ALT':226, 'LEFT_GUI':227,
              'RIGHT_CONTROL':228, 'RIGHT_SHIFT':229, 'RIGHT_ALT':230, 'RIGHT_GUI':231})
CODES.update({'F%d' % (i + 1):58 + i for i in range(12)})
CODES.update({'F%d' % (i + 13):104 + i for i in range(12)})
