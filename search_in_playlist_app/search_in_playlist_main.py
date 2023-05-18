'''
＜YouTubeの再生リスト内で動画を検索するデスクトップアプリ＞
再生リストを指定して、その再生リスト内にある動画の中から検索内容に合致する動画をピックアップし、ブラウザで表示する
cookingVerでは、動画の概要欄にある材料や分量が書かれたレシピの部分も表示する
※YouTubeのAPIキーを取得している必要がある
※非公開の再生リストにはアクセスできない

PySimpleGUI Copyright (c) 2018-2023 PySimpleGUI Authors
PySimpleGUI is licensed under LGPL-3.0
'''


import os
import re
import PySimpleGUI as sg
from search_in_playlist_mod import search_main


#グローバル変数
reg_dict ={}
reg_tb = []
reg_keys = []

#登録されているものが保存されたファイルを読み込む関数
def r_reg_file():
    global reg_dict
    file_path = os.path.dirname(__file__) + '/reg_list.txt'
    if os.path.isfile(file_path):  
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:           
                item = line.rstrip().split()
                reg_dict[item[0]] = item[1]

#登録されているものをファイルに保存する関数
def w_reg_file():
    str = ''
    for key, value in reg_dict.items():
        str += f'{key} {value}\n' 
    file_path = os.path.dirname(__file__) + '/reg_list.txt'
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(str)

#reg_tbとreg_keysをreg_dictの内容に合わせて更新する関数
def update_reg():
    global reg_tb, reg_keys
    reg_tb, reg_keys = [], []
    for key, value in reg_dict.items():
        reg_tb.append([key, value])
        reg_keys.append(key)
    

def main():
    button_size = (6, 1)
    text_size = (80, 1)
    main_text_font = ('meiryo', 20)
    head = ["        登録名        ", "          再生リストID or URL          "]
    cooking = False
    err_text = ''

    #以前登録されたものを読み込む
    r_reg_file()
    update_reg()

    #フレームのレイアウト
    #tab1,2,3のワード属性のボタンがあるフレーム
    attribute_frame_layout = [[[sg.B('[TTL]', k=f'-TTL{i}-', s=button_size), sg.B('[CH]', k=f'-CH{i}-', size=button_size), 
                                sg.B('[DESC]', k=f'-DESC{i}-', s=button_size)]] for i in range(3)]
    #tab1,2,3の検索演算子のボタンがあるフレーム
    operator_frame_layout = [[[sg.B('AND', k=f'-AND{i}-', s=button_size), sg.B('OR', k=f'-OR{i}-', size=button_size), 
                            sg.B('NOT', k=f'-NOT{i}-', s=button_size)]] for i in range(3)]
    #リスト登録の登録部分をまとめたフレーム
    reg_frame_layout = [[sg.T('登録名', size=(17, 1), justification='center', font=main_text_font), sg.Input(k='-REG_NAME-', expand_x=True, font=main_text_font)],
                        [sg.T('再生リストID or URL', size=(17, 1), justification='center', font=main_text_font), sg.Input(k='-REG_URL-', expand_x=True, font=main_text_font)],
                        [sg.B('登録', k='-REG-', size=(6, 1), font=main_text_font)]]
    #リスト登録の削除部分をまとめたフレーム
    del_frame_layout = [[sg.Listbox(reg_keys, k='-REG_LIST_DEL-', size=(47, 2), horizontal_scroll=True, select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE, font=('meiryo', 16)),
                        sg.B('削除', k='-DEL-', size=(6, 1), font=main_text_font)]]
    
    #tab1,2,3のレイアウト
    main_tab_layout = [[
        [sg.T('～～ YouTube再生リスト内検索 ～～', size=(35, 1), justification='center', font=('meiryo', 26))],
        [sg.T('APIキー', size=(17, 1), justification='center', font=main_text_font), sg.Input(k=f'-API{i}-', expand_x=True, font=main_text_font)],
        [sg.T('再生リストID or URL', size=(17, 1), justification='center', font=main_text_font), sg.Input(k=f'-PLAYLIST{i}-', expand_x=True, font=main_text_font)],
        [sg.T('(リストの中から選択)', size=(21, 1), justification='center', font=('meiryo', 16)), 
        sg.Listbox(reg_keys, size=(17, 2), k=f'-REG_LIST{i}-', bind_return_key=True, horizontal_scroll=True, expand_x=True, font=('meiryo', 16))],
        [sg.Input(k=f'-SEARCH{i}-', expand_x=True, size=(6, 1), font=main_text_font), sg.B('検索', k=f'-START{i}-', size=(6, 1), font=main_text_font)],
        [sg.Frame('ワード属性', attribute_frame_layout[i], title_location=sg.TITLE_LOCATION_TOP, 
                vertical_alignment='top', element_justification='center', grab=True), 
        sg.Frame('検索演算子', operator_frame_layout[i], title_location=sg.TITLE_LOCATION_TOP, 
                vertical_alignment='top', element_justification='center', grab=True)],
        [sg.Radio('normal ver', group_id=i, default=True, font=('meiryo', 18)), sg.Radio('cooking ver', k=f'-COOKING{i}-', group_id=i, default=False, font=('meiryo', 18))]
    ] for i in range(3)]

    #登録リストのレイアウト
    reg_layout = [
        [sg.Frame('リスト登録', reg_frame_layout, title_location=sg.TITLE_LOCATION_TOP, 
                vertical_alignment='top', element_justification='center', grab=True)],
        [sg.Frame('リストから削除', del_frame_layout, title_location=sg.TITLE_LOCATION_TOP, 
                vertical_alignment='top', element_justification='center', grab=True)],
        [sg.Table(reg_tb, k='-REG_TB-', size=(1000, 700), headings=head, alternating_row_color="#333333",
                  enable_click_events=True, vertical_scroll_only=False)]
    ]

    #検索説明のレイアウト
    manual_layout = [
        [sg.T('===ワード属性===', size=text_size)],
        [sg.T('ワードの前に属性を付けると、それについてのワードとして検索できる', size=text_size)],
        [sg.T('属性を付けない場合は、ワードはタイトルと概要欄の中で検索される', size=text_size)],
        [sg.T('【 タイトル：[TITLE] or [TTL] 】', size=text_size)],
        [sg.T('【 チャンネル：[CHANNEL] or [CH] 】', size=text_size)],
        [sg.T('【 概要欄：[DESCRIPTION] or [DESC] 】', size=text_size)],
        [sg.T('===検索演算子===', size=text_size)],
        [sg.T('【 AND検索：「 」(スペース) or「AND」or「+」(半角プラス) 】', size=text_size)],
        [sg.T('【 OR検索：「OR」or「|」(半角パイプ) 】', size=text_size)],
        [sg.T('【 NOT検索：「NOT」or「-」(半角マイナス) 】', size=text_size)],
        [sg.T('括弧で括って検索演算子の優先順位を変えることもできる', size=text_size)],
        [sg.T('===使用例===', size=text_size)],
        [sg.T('[TITLE]○○+[CH]△△ OR □□ -[DESC]⋄⋄ ', size=text_size)],
        [sg.T('⇩', size=text_size, pad=(200, 0))],
        [sg.T('タイトルに○○があるかつチャンネル名に△△がある、または、', size=text_size)],
        [sg.T('タイトルか概要欄に□□があるかつ概要欄に⋄⋄がない動画を検索', size=text_size)],
        [sg.T('また、「--ALL--」を入力すると、再生リスト内の全動画が検索結果に表示される', size=text_size)]
    ]

    #全体のレイアウト
    layout = [
        [sg.TabGroup([[sg.Tab(f'tab{i+1}', main_tab_layout[i]) for i in range(3)] 
                    +[sg.Tab('リスト登録', reg_layout), sg.Tab('検索説明', manual_layout)]], 
                    tab_location='topleft')]
    ]

    #ウインドウ生成
    window = sg.Window('YouTube再生リスト内検索', layout, font=('meiryo', 15), resizable=True, grab_anywhere=True, 
                       size=(800, 730))

    #イベントループ
    while True:
        event, values = window.read()

        #ウインドウのバツボタンを押した場合
        if event == None:
            break

        #テーブルのセルをクリックする以外はeventは1つの文字列を返す
        if type(event) != tuple:

            #エラーの時に、表示するエラー文を格納する変数
            err_text = ''

            #tab1,2,3で検索のボタンを押した場合
            if event.startswith('-START'):
                #APIキーと再生リストID,URLと検索バーが入力されている場合
                if values[f'-API{event[-2]}-'] and values[f'-PLAYLIST{event[-2]}-'] and values[f'-SEARCH{event[-2]}-']:
                    #両端の空白を取り除いて、APIキーと再生リストIDを取り出す
                    api_key = re.sub(r'^\s+|\s+$', '', values[f'-API{event[-2]}-'])
                    playlist_id_url = re.sub(r'^\s+|\s+$', '', values[f'-PLAYLIST{event[-2]}-'])
                    playlist_id = playlist_id_url.replace('https://www.youtube.com/playlist?list=','')
                    #検索バーの内容を取り出す
                    search_bar_origin = values[f'-SEARCH{event[-2]}-']
                    #normal versionか、cooking versionか、どちらなのかを受け取る
                    if values['-COOKING0-']:
                        cooking = True
                    #インポートした検索の処理をする関数を用いて検索、もし、エラーがあった時はエラーメッセージが返ってくる
                    err_text = search_main(api_key, playlist_id, search_bar_origin, cooking, str(int(event[-2])+1))
                #APIキーが入力されていない場合    
                if values[f'-API{event[-2]}-'] == '':
                    err_text += 'APIキーを入力してください\n'
                #再生リストID,URLが入力されていない場合
                if values[f'-PLAYLIST{event[-2]}-'] == '':
                    err_text += '再生リストID or URLを入力してください\n'
                #エラーがあった場合、ポップアップを出す
                if err_text:
                    sg.popup_error(err_text, title='Error', grab_anywhere=True)

            #tab1,2,3でワード属性のボタンが押された場合        
            elif event.startswith('-TTL') or event.startswith('-CH') or event.startswith('-DESC'):
                #tkinter.Entryオブジェクトから検索バーのカーソル位置を取得
                input_elem = window[f'-SEARCH{event[-2]}-'].TKEntry
                cursor_pos = input_elem.index('insert')
                #カーソル位置にワード属性を代入する
                search_bar_origin_1 = values[f'-SEARCH{event[-2]}-'][:cursor_pos]
                search_bar_origin_2 = values[f'-SEARCH{event[-2]}-'][cursor_pos:]
                search_bar_origin = f'{search_bar_origin_1} [{event[1:-2]}]{search_bar_origin_2}'
                window[f'-SEARCH{event[-2]}-'].update(search_bar_origin)
                #代入したワード属性の後ろにカーソルが来るようにする
                window[f'-SEARCH{event[-2]}-'].SetFocus()
                window[f'-SEARCH{event[-2]}-'].Widget.icursor(cursor_pos+len(event))

            #tab1,2,3で検索演算子のボタンが押された場合
            elif event.startswith('-AND') or event.startswith('-OR') or event.startswith('-NOT'):
                #tkinter.Entryオブジェクトから検索バーのカーソル位置を取得
                input_elem = window[f'-SEARCH{event[-2]}-'].TKEntry
                cursor_pos = input_elem.index('insert')
                #カーソル位置に検索演算子を代入する
                search_bar_origin_1 = values[f'-SEARCH{event[-2]}-'][:cursor_pos]
                search_bar_origin_2 = values[f'-SEARCH{event[-2]}-'][cursor_pos:]
                search_bar_origin = f'{search_bar_origin_1} {event[1:-2]} {search_bar_origin_2}'
                window[f'-SEARCH{event[-2]}-'].update(search_bar_origin)
                #代入した検索演算子の後ろにカーソルが来るようにする
                window[f'-SEARCH{event[-2]}-'].SetFocus()
                window[f'-SEARCH{event[-2]}-'].Widget.icursor(cursor_pos+len(event)-1)

            #tab1,2,3で登録したものをクリックし、再生リストID,URLに登録したものの内容を入れる場合
            elif event.startswith('-REG_LIST'):
                reg_url = reg_dict[values[f'-REG_LIST{event[-2]}-'][0]]
                window[f'-PLAYLIST{event[-2]}-'].update(reg_url)

            #リスト登録で登録ボタンが押された場合
            elif event == '-REG-':
                #登録名と再生リストID,URLが入力されている場合
                if values['-REG_NAME-'] and values['-REG_URL-']:
                    #両端の空白を取り除いて、登録名と再生リストID,URLを取り出す
                    reg_name = re.sub(r'^\s+|\s+$', '', values['-REG_NAME-'])
                    reg_url = re.sub(r'^\s+|\s+$', '', values['-REG_URL-'])
                    #登録名と再生リストの内容の中に空白を含んでいない場合、すなわち、登録が正常に行われる場合
                    if (not re.findall(' |　', reg_name)) and (not re.findall(' |　', reg_url)):    
                        reg_dict[reg_name] = reg_url
                        update_reg()
                        for i in range(3):
                            window[f'-REG_LIST{i}-'].update(reg_keys)
                        window['-REG_LIST_DEL-'].update(reg_keys)
                        window['-REG_TB-'].update(reg_tb)
                        window['-REG_NAME-'].update('')
                        window['-REG_URL-'].update('')
                    #登録名の内容の中に空白を含んでいる場合
                    if re.findall(' |　', reg_name):
                        err_text += '登録名の中に空白を入れないでください\n'
                    #再生リストID,URLの内容の中に空白を含んでいる場合
                    if re.findall(' |　', reg_url):
                        err_text += '再生リストID or URLの中に空白を入れないでください\n'
                #登録名が入力されていない場合
                if values['-REG_NAME-'] == '':
                    err_text += '登録名を入力してください\n'
                #再生リストID,URLが入力されていない場合
                if values['-REG_URL-'] == '':
                    err_text += '再生リストID or URLを入力してください\n'
                #エラーがあった場合、ポップアップを出す
                if err_text:
                    sg.popup_error(err_text, title='Error', grab_anywhere=True)
                
            #リスト登録で削除ボタンが押された場合    
            elif event == '-DEL-':
                del_text = '下記の登録を削除しますか？\n'
                for del_item in values['-REG_LIST_DEL-']:
                    del_text += f'{del_item}\n'
                #削除としてクリックしたものを本当に削除してよいのかの確認
                ans = sg.popup_ok_cancel(del_text, title='削除')
                #確認でOKボタンが押された場合、実行する
                if ans == 'OK':
                    for del_item in values['-REG_LIST_DEL-']:
                        reg_dict.pop(del_item)
                    update_reg()
                    for i in range(3):
                        window[f'-REG_LIST{i}-'].update(reg_keys)
                    window['-REG_LIST_DEL-'].update(reg_keys)
                    window['-REG_TB-'].update(reg_tb)
                    window['-REG_NAME-'].update('')
                    window['-REG_URL-'].update('')
        
         #テーブルのセルをクリックした場合、それについての内容をポップアップで表示する
        else:
            row, col = event[2]
            if col == 0:
                sg.popup(f'登録名：\n{reg_tb[row][col]}', title='登録名', grab_anywhere=True)
            elif col == 1:
                sg.popup(f'再生リストID or URL：\n{reg_tb[row][col]}', title='再生リストID or URL', grab_anywhere=True)

    #イベントループを抜けたので、登録されているものの内容をファイルに書き込み、保存して、ウインドウを閉じる
    w_reg_file()
    window.close()


if __name__ == '__main__':
    main()