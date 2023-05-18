'''
search_in_playlist_main.pyに使うモジュール
検索の処理についてのコードを書いている
'''


import urllib.request
import urllib.parse
import json
import os
import re
import webbrowser


#ひらがなとカタカナの相互変換、アルファベットの変換をした単語のリストを生成する関数
def word_trans(word):
    #検索したいワードを得るため
    word = word.replace('[TTL]', '')
    word = word.replace('[TITLE]', '')
    word = word.replace('[CH]', '')
    word = word.replace('[CHANNEL]', '')
    word = word.replace('[DESC]', '')
    word = word.replace('[DESCRIPTION]', '')
    
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

#入力された検索ワードを読み込んで、これから検索する上で必要な形に加工する関数
def search_word_analysis(search_bar_origin):
    #ワード属性の使い方が正しくない場合
    search_bar = search_bar_origin + ' '
    if re.findall('\[TTL\] |\[TTL\]　|\[CH\] |\[CH\]　|\[DESC\] |\[DESC\]　|\[TITLE\] |\[TITLE\]　|\[CHANNEL\] |\[CHANNEL\]　|\[DESCRIPTION\] |\[DESCRIPTION\]　', search_bar):
        return None
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
    NOT_close = 0
    judge = ''
    word_judge, word_judge_ttl, word_judge_ch, word_judge_desc = {}, {}, {}, {}
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
            NOT_close += 1
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
                if word.find('[TTL]') == 0 or word.find('[TITLE]') == 0:
                    word_judge_ttl[word_i] = True
                elif word.find('[CH]') == 0 or word.find('[CHANNEL]') == 0:
                    word_judge_ch[word_i] = True
                elif word.find('[DESC]') == 0 or word.find('[DESCRIPTION]') == 0:
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
                if word.find('[TTL]') == 0 or word.find('[TITLE]') == 0:
                    judge += "word_judge_ttl['" + word_i + "']"
                elif word.find('[CH]') == 0 or word.find('[CHANNEL]') == 0:
                    judge += "word_judge_ch['" + word_i + "']"
                elif word.find('[DESC]') == 0 or word.find('[DESCRIPTION]') == 0:
                    judge += "word_judge_desc['" + word_i + "']"
                else:
                    judge += "word_judge['" + word_i + "']"
                #wordsが途中ならば+でつなぎ、最後ならば括弧を閉じる
                if words[-1] == word_i:
                    judge += ')'
                else:
                    judge += ' + '
            space_flag = True
        if NOT_close > 0:
            NOT_close += 1
            if NOT_close == 3:
                judge += ')'
                NOT_close = 0
    #「AND OR」,「OR OR」と連続している場合
    if re.findall('\*  \+|\+  \+', judge):
        return None
    #judgeが数式として扱えるかテスト
    try:
        eval(judge)
    except Exception:
        return None        
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
def word_in_video(item_snippet, word_judge, word_judge_ttl, word_judge_ch, word_judge_desc):
    #動画のタイトルか概要欄に検索ワードが含まれているか判定
    for word in word_judge.keys():
        if (word in item_snippet['description']) or (word in item_snippet['title']):
            word_judge[word] = True
        else:
            word_judge[word] = False
    #動画のタイトルに検索ワードが含まれているか判定
    for word in word_judge_ttl.keys():
        if word in item_snippet['title']:
            word_judge_ttl[word] = True
        else:
            word_judge_ttl[word] = False
    #動画のチャンネル名に検索ワードが含まれているか判定
    for word in word_judge_ch.keys():
        if word in item_snippet['videoOwnerChannelTitle']:
            word_judge_ch[word] = True
        else:
            word_judge_ch[word] = False
    #動画の概要欄に検索ワードが含まれているか判定
    for word in word_judge_desc.keys():
        if word in item_snippet['description']:
            word_judge_desc[word] = True
        else:
            word_judge_desc[word] = False
    return word_judge, word_judge_ttl, word_judge_ch, word_judge_desc

#動画の概要欄の料理の材料と分量が書いてあるところを抽出する関数
def ingredient(desc_part):
    #下のワードで料理の材料と分量が書かれているところかを判定する
    ok_key = ['適量']
    #下のワードで料理の材料と分量が書かれていないところかを判定する
    not_key = ['http']
    ingredient_list = []
    for part in desc_part:
        key_judge = False
        #料理の材料と分量が書かれているところかを単位の表記があるかでも判定する
        if re.findall('\dg|\dｇ|\dcm|\dｃｍ|\dcc|\dｃｃ|\dml|\dｍｌ|\d本|\d個|\d枚|\d袋|大さじ\d|大匙\d|小さじ\d|小匙\d|スプーン\d', part):
            key_judge = True
        if key_judge:
            for word in not_key:
                if word in part:
                    key_judge = False
        if not key_judge:
            for word in ok_key:
                if word in part:
                    key_judge = True
        if key_judge:
            ingredient_list.append(part)
    return ingredient_list

#検索にヒットした時の処理をする関数
def hit(item_snippet, cooking):
    ingredients = ''
    if cooking:
        #概要欄の情報を改行や「ーー」や「--」や「]」で区切る
        desc_part = re.split('ー+\n+|-+\n+|\n\n+|\n\s+\n+|]\n+', item_snippet['description'])
        #区切ったところの単位で、料理の材料と分量について書かれているところかを判定する
        ing_list = ingredient(desc_part)
        ingredients = '<br>'.join(ing_list)
        ingredients = ingredients.replace('\n', '<br>')

    #htmlで動画タイトル、チャンネル、動画のURL、料理の材料や分量の情報、サムネイルを表示する部分 
    html_body_part = '''
    <article>
    <h3>{title_colon}<a href="{url}" target="_blank" rel="noopener noreferrer">{title}</a></h3>
    <p>{channel}</p>
    <p>{ingredient}</p>
    <img src="{img}" alt="{thumbnail}">
    </article>
    <br>
    '''.format(title_colon = 'Title：',
               url = 'https://www.youtube.com/watch?v='+str(item_snippet['resourceId']['videoId']),
               title = str(item_snippet['title']),
               channel = 'Channel：'+str(item_snippet['videoOwnerChannelTitle']),
               ingredient = ingredients,
               img = item_snippet['thumbnails']['medium']['url'],
               thumbnail = 'サムネイル'
               )
    return html_body_part

#再生リストのタイトル、検索ワード、ヒット件数を入れたヘッダーを作成する関数
def html_body_header(playlist_ttl, search_bar_origin, item_count, hit_count):
    header = '''
    <header>
    <h3>{}<br>{}</h3>
    <p>{}件中{}件ヒット</P>
    </header>
    '''.format('再生リスト：' + str(playlist_ttl),
                '検索ワード：' + search_bar_origin,
                str(item_count),
                str(hit_count))
    return header

#htmlのファイルを作成する関数
def html_file(body, tab_num):
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
    '''.format(f'tab{tab_num}_YouTube再生リスト内検索', body)
    file_path = os.path.dirname(__file__) + f'/search_in_playlist_tab{tab_num}.html'
    with open( file_path, 'w', encoding='utf-8' ) as f: 
        f.write(str)
    return file_path

#検索のメインとなる関数   
def search_main(api_key, playlist_id, search_bar_origin, cooking, tab_num):
    nextPageToken = ''
    item_count = 0
    hit_count = 0
    html_body_main = ''
    if search_bar_origin != "--ALL--":
        judges = search_word_analysis(search_bar_origin)
        if judges:
            judge, word_judge, word_judge_ttl, word_judge_ch, word_judge_desc = judges
        else:
            return '検索ルールに違反しています\n検索説明のページで説明を読んでください'
    try:
        while True:
            #playlist内の最大50件分の動画情報を取得
            target_body = data_req('playlistItems', playlist_id, api_key, nextPageToken)
            #再生リスト内の動画の数を記録
            item_count += len(target_body['items'])

            #1つ1つ動画を調べていく
            for item in target_body['items']:
                if search_bar_origin != "--ALL--":
                    #ワードが含まれているかの情報を代入
                    word_judge, word_judge_ttl, word_judge_ch, word_judge_desc = word_in_video(item['snippet'], word_judge, word_judge_ttl, word_judge_ch, word_judge_desc)
                    #ヒットか判定する式にワードが含まれているか/いないかの情報を入れて、数式にし、１以上ならばその動画はヒット
                    if eval(judge) > 0:
                        html_body_main += hit(item['snippet'], cooking)
                        #ヒットした動画数を記録
                        hit_count += 1
                #検索バーに「--ALL--」が入力されたら、再生リスト内の全動画をヒットさせる
                elif search_bar_origin == "--ALL--":
                    html_body_main += hit(item['snippet'], cooking)
                    hit_count += 1

            #再生リスト内にまだ調べていない動画があるか判定
            if 'nextPageToken' in target_body:
                nextPageToken = target_body['nextPageToken']
            else:
                #playlistの情報を取得
                target_body = data_req('playlists', playlist_id, api_key, nextPageToken)
                html_body = html_body_header(target_body['items'][0]['snippet']['title'], search_bar_origin, item_count, hit_count)
                html_body += html_body_main
                #結果をhtmlファイルにする
                html_file_path = html_file(html_body, tab_num)
                #そのhtmlファイルをブラウザで開く
                webbrowser.open(html_file_path)
                break
        return None

    except urllib.error.HTTPError as err:
        if err.code == 400:
            return 'APIキーが有効ではありません'
        if err.code == 404:
            return '再生リストが見つかりません'

    except Exception as err:
        return str(err)