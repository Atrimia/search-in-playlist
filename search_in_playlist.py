'''
＜YouTubeの再生リスト内で動画を検索するツール＞
再生リストを指定して、その再生リスト内にある動画の中から検索内容に合致する動画をピックアップし、ブラウザで表示する
※YouTubeのAPIキーを取得している必要がある
※非公開の再生リストにはアクセスできない
'''


import urllib.request
import urllib.parse
import json
import os
import webbrowser


#＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊

#APIキーと、再生リストID or 再生リストのURLの保存用（空のままだと実行時に入力になる）
API_KEY = ''
PLAYLIST_ID_URL = ''

#＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊


#検索の仕方の説明を表示する関数
def explanation():
    print('---検索演算子の説明---')
    print('【AND検索：「 」(スペース) or「AND」or「+」(半角プラス)】【OR検索：「OR」or「|」(半角パイプ)】【NOT検索：「NOT」or「-」(半角マイナス)】 で単語をつなぐ')
    print('括弧で括って検索演算子の優先順位を変えることもできる')
    print('ワードの前に属性(タイトル：[title] or [ttl], チャンネル：[channel] or [ch], 概要欄：[description] or [desc])を付けると、それについてのワードとして検索できる')
    print('属性を付けない場合は、ワードはタイトルと概要欄の中で検索される')
    print('(例) [title]○○+[ch]▵▵ OR □□ -[desc]⋄⋄ ⇒ タイトルに○○があるかつチャンネル名に▵▵がある、または、タイトルか概要欄に□□があるかつ概要欄に⋄⋄がない動画を検索')
    print('----------------------')

#ひらがなとカタカナの相互変換、アルファベットの変換をした単語のリストを生成する関数
def word_trans(word):
    #検索したいワードを得るため
    word = word.replace('[ttl]', '')
    word = word.replace('[title]', '')
    word = word.replace('[ch]', '')
    word = word.replace('[channel]', '')
    word = word.replace('[desc]', '')
    word = word.replace('[description]', '')
    
    words = [word]
    #カタカナからひらがなへの辞書
    katakana_to_hiragana_dict = {chr(i): chr(i - 96) for i in range(ord('ァ'), ord('ヺ'))}
    #ひらがなからカタカナへの辞書
    hiragana_to_katakana_dict = {chr(i): chr(i + 96) for i in range(ord('ぁ'), ord('ゖ'))}
    #カタカナからひらがなに変換
    words.append(''.join([katakana_to_hiragana_dict.get(c, c) for c in word]))
    #ひらがなからカタカナに変換
    words.append(''.join([hiragana_to_katakana_dict.get(c, c) for c in word]))
    #アルファベットについての変換
    words.append(word.capitalize())
    words.append(word.upper())
    words.append(word.lower())
    #リストの要素で重複しているのは消す
    return list(set(words))

#入力された検索ワードを読み込んで、これから検索する上で必要な形に加工する
def search_word_analysis(search_bar_origin):
    #split()で分けるための加工
    search_bar = search_bar_origin.replace('(', ' ( ')
    search_bar = search_bar.replace(')', ' ) ')
    search_bar = search_bar.replace('（', ' ( ')
    search_bar = search_bar.replace('）', ' ) ')
    search_bar = search_bar.replace('+', ' + ')
    search_bar = search_bar.replace(' -', ' - ')
    search_bar = search_bar.replace('　-', ' - ')      
    #ワードと検索演算子を１つずつ分ける
    search_words = search_bar.split()
    space_flag = False
    close = 0
    judge = ''
    word_judge = {}
    word_judge_ttl = {}
    word_judge_ch = {}
    word_judge_desc = {}
    #検索演算子を算術演算子に変換させた文字列の式を作成
    for word in search_words:
        if (word == 'AND') or (word == '+'):
            judge += ' * '
            space_flag = False
        elif (word == 'OR') or (word == '|'):
            judge += ' + '
            space_flag = False
        elif (word == 'NOT') or (word == '-'):
            judge += ' * (not '
            space_flag = False
            close += 1
        elif word == '(':
            if space_flag:
                judge += ' * ('
            else:
                judge += ' ('
            space_flag = False
        elif word == ')':
            judge += ') '
        else:    
            words = word_trans(word)
            for word_i in words:
                #それぞれに対応した辞書にwordの情報を入れる
                if word.find('[ttl]') == 0 or word.find('[title]') == 0:
                    word_judge_ttl[word_i] = True
                elif word.find('[ch]') == 0 or word.find('[channel]') == 0:
                    word_judge_ch[word_i] = True
                elif word.find('[desc]') == 0 or word.find('[description]') == 0:
                    word_judge_desc[word_i] = True
                else:
                    word_judge[word_i] = True
                #先頭に括弧を付ける。もし、space_flagがTrue、すなわち、検索ワードが空白区切りで連続していたら*を加える
                if words[0] == word_i:
                    if space_flag:
                        judge += ' * ('
                    else:
                        judge += '('
                #judgeにそれぞれに対応した辞書の形で文字列として加えておく
                if word.find('[ttl]') == 0 or word.find('[title]') == 0:
                    judge += "word_judge_ttl['" + word_i + "']"
                elif word.find('[ch]') == 0 or word.find('[channel]') == 0:
                    judge += "word_judge_ch['" + word_i + "']"
                elif word.find('[desc]') == 0 or word.find('[description]') == 0:
                    judge += "word_judge_desc['" + word_i + "']"
                else:
                    judge += "word_judge['" + word_i + "']"
                #wordsが途中ならば+でつなぎ、最後ならば括弧を閉じる
                if words[-1] == word_i:
                    judge += ')'
                else:
                    judge += ' + '
            space_flag = True
        if close > 0:
            close += 1
            if close == 3:
                judge += ')'
                close = 0
    return judge, word_judge, word_judge_ttl, word_judge_ch, word_judge_desc

#情報を取得する関数
def data_req(method, playlist_id, api_key, nextPageToken):
    if method == 'playlistItems':
        #YouTube APIのplaylistItemsメソッドでplaylist内の動画情報を最大50件分取得
        param = {
            'part':'snippet',
            'playlistId':playlist_id,
            'maxResults':50,
            'pageToken':nextPageToken,
            'key':api_key
        }
    elif method == 'playlists':
        #YouTube APIのplaylistsメソッドでplaylistの情報を取得
        param = {
            'part':'snippet',
            'id':playlist_id,
            'key':api_key
        }
    target_url = 'https://www.googleapis.com/youtube/v3/' + method + '?'+urllib.parse.urlencode(param) 
    req = urllib.request.Request(target_url)
    with urllib.request.urlopen(req) as res:
        target_body = json.load(res)
    return target_body

#動画情報の中に検索ワードが含まれているか判定する関数
def word_in_movie(item, word_judge, word_judge_ttl, word_judge_ch, word_judge_desc):
    #動画のタイトルか概要欄に検索ワードが含まれているか判定
    for word in word_judge.keys():
        if (word in item['snippet']['description']) or (word in item['snippet']['title']):
            word_judge[word] = True
        else:
            word_judge[word] = False
    #動画のタイトルに検索ワードが含まれているか判定
    for word in word_judge_ttl.keys():
        if word in item['snippet']['title']:
            word_judge_ttl[word] = True
        else:
            word_judge_ttl[word] = False
    #動画のチャンネル名に検索ワードが含まれているか判定
    for word in word_judge_ch.keys():
        if word in item['snippet']['videoOwnerChannelTitle']:
            word_judge_ch[word] = True
        else:
            word_judge_ch[word] = False
    #動画の概要欄に検索ワードが含まれているか判定
    for word in word_judge_desc.keys():
        if word in item['snippet']['description']:
            word_judge_desc[word] = True
        else:
            word_judge_desc[word] = False
    return word_judge, word_judge_ttl, word_judge_ch, word_judge_desc

#検索にヒットした時の処理をする関数
def hit(**kwargs):
    #htmlで動画タイトル、チャンネル、動画のURL、サムネイルを表示する部分 
    html_body_part = '''
    <article>
    <h3>{title_colon}<a href="{url}" target="_blank" rel="noopener noreferrer">{title}</a></h3>
    <p>{channel}</p>
    <img src="{img}" alt="{thumbnail}">
    </article>
    <br>
    '''.format(title_colon = 'Title：',
               url = 'https://www.youtube.com/watch?v='+str(kwargs['snippet']['resourceId']['videoId']),
               title = str(kwargs['snippet']['title']),
               channel = 'Channel：'+str(kwargs['snippet']['videoOwnerChannelTitle']),
               img = kwargs['snippet']['thumbnails']['medium']['url'],
               thumbnail = 'サムネイル'
               )
    return html_body_part

#再生リストのタイトル、検索ワード、ヒット件数を入れたヘッダーを作成する関数
def html_body_header(target_body, search_bar_origin, item_count, hit_count):
    header = '''
    <header>
    <h3>{}<br>{}</h3>
    <p>{}件中{}件ヒット</P>
    </header>
    '''.format('再生リスト：' + str(target_body['items'][0]['snippet']['title']),
                '検索ワード：' + search_bar_origin,
                str(item_count),
                str(hit_count))
    return header

#htmlのファイルを作成する関数
def html_file(body):
    str = '''
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <title>{}</title>
    </head>
    <body>
    {} 
    </body>
    </html>
    '''.format('YouTube再生リスト内検索', body)
    file_path = os.path.dirname(__file__) + '/search_in_playlist.html'
    with open( file_path, 'w', encoding='utf-8' ) as f: 
        f.write(str)
    return file_path


def main():
    while_count = 1
    nextPageToken = ''
    item_count = 0
    hit_count = 0
    html_body_main = ''

    while while_count > 0:

        api_key = ''
        playlist_id_url = ''

        #APIキーを取得
        if API_KEY == '':
            while api_key == '':
                api_key = input('APIキー：')
        else:
            api_key = API_KEY

        #再生リストIDを取得
        if PLAYLIST_ID_URL == '':
            while playlist_id_url == '':
                playlist_id_url = input('再生リストID or URL：')
        else:
            playlist_id_url = PLAYLIST_ID_URL
        playlist_id = playlist_id_url.replace('https://www.youtube.com/playlist?list=','')

        #ヒットか判定する式を作成    
        if while_count == 1:
            explanation()
            search_bar_origin = ''
            while search_bar_origin == '':
                search_bar_origin = input('検索ワード：')
            judge, word_judge, word_judge_ttl, word_judge_ch, word_judge_desc = search_word_analysis(search_bar_origin)

        try:
            while True:
                #playlist内の最大50件分の動画情報を取得
                target_body = data_req('playlistItems', playlist_id, api_key, nextPageToken)
                #再生リスト内の動画の数を記録
                item_count += len(target_body['items'])

                #1つ1つ動画を調べていく
                for item in target_body['items']:
                    #ワードが含まれているかの情報を代入
                    word_judge, word_judge_ttl, word_judge_ch, word_judge_desc = word_in_movie(item, word_judge, word_judge_ttl, word_judge_ch, word_judge_desc)
                    #ヒットか判定する式にワードが含まれているか/いないかの情報を入れて、数式にし、１以上ならばその動画はヒット
                    if eval(judge) > 0:
                        html_body_main += hit(**item)
                        #ヒットした動画数を記録
                        hit_count += 1    

                #再生リスト内にまだ調べていない動画があるか判定
                if 'nextPageToken' in target_body:
                    nextPageToken = target_body['nextPageToken']
                else:
                    #playlistの情報を取得
                    target_body = data_req('playlists', playlist_id, api_key, nextPageToken)
                    html_body = html_body_header(target_body, search_bar_origin, item_count, hit_count)
                    html_body += html_body_main
                    #結果をhtmlファイルにする
                    html_file_path = html_file(html_body)
                    #そのhtmlファイルをブラウザで開く
                    webbrowser.open(html_file_path)
                    break

        except urllib.error.HTTPError as err:
            print('Error：' + str(err))
            if (err.code == 400) or (err.code == 403) or (err.code == 404):
                print('APIキー、または、再生リストIDが正しく入力されていない可能性があります')
                if (API_KEY == '') or (PLAYLIST_ID_URL == ''):
                    print('もう一度入力してください')
                    while_count += 1
                    continue

        except Exception as err:
            print('Error：' + str(err))
        
        break


if __name__ == '__main__':
    main()