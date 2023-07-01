import PySimpleGUI as psg
from src.modules.tf2e.lobby import TF2Player

psg.theme_previewer()
# names = ["help", "this", "sux"]
# lst = psg.Combo(TF2Player.possible_associations, font=('Arial Bold', 14), default_value="help", expand_x=True, enable_events=True, readonly=True, key='-COMBO-')
# layout = [[lst,
#            psg.Button('Add', ),
#            psg.Button('Remove'),
#            psg.Button('Exit')],
#           [psg.Text("", key='-MSG-',
#                     font=('Arial Bold', 14),
#                     justification='center')]
#           ]
# ch = ""
# val = ""
# window = psg.Window('Combobox Example', layout, size=(715, 200))
# while True:
#     event, values = window.read()
#     print(event, values)
#     if event in (psg.WIN_CLOSED, 'Exit'):
#         break
#     if event == 'Add':
#         names.append(values['-COMBO-'])
#         print(names)
#         window['-COMBO-'].update(values=names, value=values['-COMBO-'])
#         msg = "A new item added : {}".format(values['-COMBO-'])
#         window['-MSG-'].update(msg)
#
#     # window['-COMBO-'].update(values=names, value=' ')
#     msg = "A new item removed : {}".format(val)
#     window['-MSG-'].update(msg)
# window.close()
