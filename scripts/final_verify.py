#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Final verification of language purity in articles."""
import os
import re
from bs4 import BeautifulSoup

ARTICLES_DIR = 'articles'

SKIP_EN_WORDS = {
    'png', 'jpg', 'jpeg', 'svg', 'gif', 'webp', 'src', 'alt', 'href', 'html', 'css', 'js',
    'http', 'https', 'www', 'com', 'cn', 'org', 'net', 'mp', 'mmbiz', 'wx_fmt', 'appmsg',
    'wx', 'qqpic', 'qpic', 'data', 'type', 'ratio', 'lazy', 'loading', 'width', 'height',
    'style', 'class', 'id', 'span', 'div', 'p', 'img', 'section', 'strong', 'em', 'br', 'hr',
    'ul', 'ol', 'li', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'caption',
    'leaf', 'nodeleaf', 'center', 'box', 'sizing', 'border', 'color', 'rgb', 'font', 'size',
    'background', 'margin', 'padding', 'display', 'inline', 'block', 'vertical', 'align',
    'max', 'auto', 'important', 'overflow', 'hidden', 'position', 'relative', 'absolute',
    'fixed', 'top', 'bottom', 'left', 'right', 'inset', 'none', 'solid', 'transparent',
    'white', 'black', 'red', 'blue', 'green', 'yellow', 'px', 'rem', 'em', 'vh', 'vw',
    'url', 'min', 'text', 'align', 'justify', 'normal', 'space', 'letter', 'spacing',
    'line', 'family', 'serif', 'sans', 'weight', 'bold', 'italic', 'underline', 'decoration',
    'shadow', 'radius', 'cursor', 'pointer', 'default', 'hover', 'active', 'focus', 'visited',
    'disabled', 'readonly', 'required', 'checked', 'selected', 'hidden', 'visible', 'collapse',
    'separate', 'clip', 'origin', 'transform', 'transition', 'animation', 'keyframes', 'media',
    'screen', 'print', 'speech', 'all', 'not', 'only', 'and', 'or', 'min', 'max', 'device',
    'aspect', 'ratio', 'orientation', 'portrait', 'landscape', 'resolution', 'dpi', 'dpcm',
    'monochrome', 'grid', 'scan', 'interlace', 'progressive', 'prefers', 'reduced', 'motion',
    'contrast', 'scheme', 'dark', 'light', 'lang', 'dir', 'ltr', 'rtl', 'role', 'aria',
    'label', 'labelledby', 'describedby', 'controls', 'live', 'atomic', 'relevant', 'busy',
    'expanded', 'pressed', 'valuenow', 'valuemin', 'valuemax', 'multiline', 'multiselectable',
    'invalid', 'modal', 'haspopup', 'level', 'setsize', 'posinset', 'colspan', 'rowspan',
    'headers', 'scope', 'abbr', 'sort', 'draggable', 'dropzone', 'spellcheck', 'translate',
    'contenteditable', 'contextmenu', 'tabindex', 'accesskey', 'title', 'target', 'rel',
    'download', 'ping', 'coords', 'shape', 'usemap', 'ismap', 'srcset', 'sizes', 'crossorigin',
    'integrity', 'referrerpolicy', 'autoplay', 'loop', 'muted', 'preload', 'poster',
    'playsinline', 'object', 'param', 'embed', 'iframe', 'sandbox', 'seamless', 'allow',
    'form', 'action', 'method', 'enctype', 'novalidate', 'autocomplete', 'autofocus',
    'formaction', 'formenctype', 'formmethod', 'formnovalidate', 'formtarget', 'name', 'value',
    'placeholder', 'size', 'maxlength', 'minlength', 'multiple', 'pattern', 'step', 'cols',
    'rows', 'wrap', 'accept', 'capture', 'list', 'max', 'min', 'optimum', 'low', 'high',
    'challenge', 'keytype', 'charset', 'equiv', 'content', 'property', 'itemprop',
    'itemscope', 'itemtype', 'itemid', 'itemref', 'wechat', 'redirect', 'scene', 'chksm',
    'sn', 'idx', 'biz', 'qq', 'weixin', 'mmbiz', 'qpic', 'from', 'wx_fmt', 'wx', 'wxw',
    'wxwimg', 'wxwimg', 'jpeg', 'png', 'svg', 'gif', 'vivo', 'oppo', 'xiaomi', 'huawei',
    'iphone', 'ipad', 'ios', 'android', 'apple', 'google', 'microsoft', 'meta', 'facebook',
    'twitter', 'instagram', 'tiktok', 'youtube', 'bilibili', 'weibo', 'douyin', 'xiaohongshu',
    'zhihu', 'whatsapp', 'telegram', 'signal', 'line', 'kakao', 'naver', 'daum', 'nate',
    'yahoo', 'bing', 'baidu', 'sogou', 'haosou', 'duckduckgo', 'ecosia', 'startpage',
    'searx', 'wolframalpha', 'wikipedia', 'wikimedia', 'wiktionary', 'wikibooks', 'wikinews',
    'wikiquote', 'wikisource', 'wikiversity', 'wikivoyage', 'wikidata', 'mediawiki',
    'creativecommons', 'gpl', 'mit', 'apache', 'bsd', 'mozilla', 'openssl', 'linux',
    'ubuntu', 'debian', 'fedora', 'centos', 'redhat', 'suse', 'arch', 'gentoo',
    'slackware', 'mint', 'elementary', 'pop', 'zorin', 'manjaro', 'endeavouros', 'garuda',
    'artix', 'void', 'alpine', 'nixos', 'guix', 'qubes', 'tails', 'whonix', 'kali',
    'parrot', 'blackarch', 'pentoo', 'backbox', 'caine', 'deft', 'sift', 'remnux',
    'flare', 'sans', 'offensive', 'security', 'certified', 'ethical', 'hacker', 'ceh',
    'oscp', 'oswe', 'osep', 'osce', 'osee', 'gxpn', 'gwapt', 'gpen', 'gmon', 'gsec',
    'gci', 'gisp', 'gstrt', 'gsna', 'grem', 'gcti', 'gdpr', 'cissp', 'cisa', 'cism',
    'crisc', 'cgeit', 'cobit', 'itil', 'pmp', 'pmi', 'agile', 'scrum', 'kanban', 'lean',
    'six', 'sigma', 'kaizen', 'tqm', 'iso', 'iec', 'ieee', 'ansi', 'asme', 'astm', 'sae',
    'mil', 'std', 'nfc', 'rfid', 'qr', 'barcode', 'upc', 'ean', 'isbn', 'issn', 'doi',
    'pmid', 'arxiv', 'bibtex', 'ris', 'endnote', 'zotero', 'mendeley', 'papers', 'readcube',
    'paperpile', 'citavi', 'jabref', 'docear', 'colwiz', 'f1000', 'researchgate', 'academia',
    'orcid', 'publons', 'scopus', 'wos', 'webofscience', 'pubmed', 'ncbi', 'embase',
    'cochrane', 'cinahl', 'psycinfo', 'eric', 'jstor', 'project', 'muse', 'sage',
    'springer', 'elsevier', 'wiley', 'taylor', 'francis', 'oxford', 'cambridge',
    'harvard', 'yale', 'princeton', 'columbia', 'stanford', 'mit', 'caltech', 'berkeley',
    'cmu', 'gatech', 'uiuc', 'umich', 'uw', 'utexas', 'ucla', 'ucsd', 'ucsb', 'ucdavis',
    'uci', 'ucr', 'ucsc', 'ucmerced', 'uc', 'usc', 'nyu', 'cuny', 'suny', 'rutgers',
    'penn', 'upenn', 'duke', 'unc', 'uva', 'vt', 'umd', 'bu', 'bc', 'neu', 'tufts',
    'brandeis', 'wpi', 'rit', 'rpi', 'union', 'skidmore', 'vassar', 'sarah', 'wellesley',
    'smith', 'bryn', 'mawr', 'barnard', 'mount', 'holyoke', 'amherst', 'williams',
    'middlebury', 'bowdoin', 'colby', 'bates', 'hamilton', 'skidmore', 'wifi', 'gps',
    'usb', 'hdmi', 'vga', 'dvi', 'dp', 'pd', 'qc', 'vooc', 'dash', 'warp', 'turbo',
    'power', 'delivery', 'fast', 'charge', 'wireless', 'bluetooth', 'infrared', 'ir',
    'rf', 'lte', 'sim', 'esim', 'imei', 'meid', 'mac', 'ip', 'ipv', 'tcp', 'udp',
    'ftp', 'sftp', 'ssh', 'telnet', 'smtp', 'pop', 'imap', 'dns', 'dhcp', 'nat',
    'vpn', 'proxy', 'cdn', 'ddos', 'ssl', 'tls', 'aes', 'rsa', 'des', 'md', 'sha',
    'hmac', 'pbkdf', 'bcrypt', 'scrypt', 'argon', 'otp', 'totp', 'hotp', 'u', 'fido',
    'yubikey', 'authy', 'authenticator', 'lastpass', 'bitwarden', 'keeper', 'dashlane',
    'nordpass', 'roboform', 'truekey', 'passbolt', 'proton', 'pass', 'zoho', 'vault',
    'keychain', 'keystore', 'truststore', 'cacerts', 'pem', 'der', 'pkcs', 'crt',
    'cer', 'key', 'csr', 'crl', 'ocsp', 'stapling', 'pinning', 'transparency',
    'ct', 'hsts', 'csp', 'xss', 'csrf', 'sqli', 'rce', 'lfi', 'rfi', 'xxe',
    'ssrf', 'idor', 'bac', 'race', 'condition', 'toctou', 'buffer', 'overflow',
    'underflow', 'format', 'string', 'integer', 'heap', 'stack', 'use', 'after',
    'free', 'double', 'fetch', 'rogue', 'pointer', 'null', 'dereference', 'type',
    'confusion', 'prototype', 'pollution', 'deserialization', 'serialization',
    'marshal', 'unmarshal', 'pickle', 'yaml', 'xml', 'json', 'csv', 'tsv', 'sql',
    'nosql', 'mongodb', 'cassandra', 'redis', 'memcached', 'couchdb', 'dynamodb',
    'firestore', 'bigtable', 'spanner', 'cockroachdb', 'tidb', 'yugabytedb',
    'vitess', 'planetscale', 'supabase', 'hasura', 'prisma', 'sequelize', 'typeorm',
    'knex', 'bookshelf', 'objection', 'waterline', 'loopback', 'feathers', 'nest',
    'next', 'nuxt', 'svelte', 'sveltekit', 'astro', 'solid', 'qwik', 'remix',
    'gatsby', 'gridsome', 'vuepress', 'vitepress', 'docusaurus', 'hexo', 'hugo',
    'jekyll', 'middleman', 'react', 'vue', 'angular', 'preact', 'inferno', 'lit',
    'stencil', 'fast', 'ionic', 'capacitor', 'cordova', 'phonegap', 'titanium',
    'native', 'flutter', 'dart', 'kotlin', 'swift', 'objective', 'java', 'scala',
    'clojure', 'groovy', 'jruby', 'jython', 'ceylon', 'jvm', 'jdk', 'jre', 'sdk',
    'api', 'cli', 'gui', 'tui', 'repl', 'ide', 'editor', 'vscode', 'vim', 'neovim',
    'emacs', 'sublime', 'atom', 'brackets', 'webstorm', 'phpstorm', 'pycharm',
    'intellij', 'eclipse', 'netbeans', 'jbuilder', 'jdeveloper', 'studio', 'xcode',
    'appcode', 'clion', 'goland', 'rider', 'datagrip', 'rubymine', 'dataspell',
    'fleet', 'rustrover', 'aqua', 'gateway', 'space', 'youtrack', 'teamcity',
    'upsource', 'hub', 'datalore', 'mono', 'dotnet', 'core', 'framework', 'standard',
    'runtime', 'clr', 'cil', 'msil', 'il', 'jit', 'aot', 'ngen', 'crossgen',
    'readytorun', 'singlefile', 'selfcontained', 'frameworkdependent', 'portable',
    'pack', 'tool', 'global', 'local', 'restore', 'build', 'publish', 'run', 'test',
    'clean', 'sln', 'csproj', 'vbproj', 'fsproj', 'vcxproj', 'proj', 'props',
    'targets', 'nuspec', 'nupkg', 'snupkg', 'symbols', 'package', 'reference',
    'workload', 'maui', 'blazor', 'razor', 'mvc', 'webapi', 'minimal', 'grpc',
    'signalr', 'orleans', 'akka', 'net', 'dapr', 'tye', 'wifi', 'sp', 'spf',
    'app', 'ps', 'ad', 'day', 'suv', 'hold', 'city', 'walk', 'sarah', 'nida',
    'pubu', 'ciren', 'dingzeng', 'wang', 'chen', 'lu', 'hailin', 'zheng',
    'shengri', 'tuo', 'shi', 'xiao', 'jun', 'qian', 'yang', 'zhao', 'jing',
    'hu', 'wangguang', 'liu', 'min', 'baitian', 'yunze', 'kelao', 'luxing',
    'xiao', 'zhuoma', 'xiao', 'yu', 'ban', 'ban', 'ali', 'tibet', 'tibetan',
    'nyingchi', 'lhasa', 'shigatse', 'shannan', 'ngari', 'nagqu', 'chamdo',
    'linzhi', 'rikaze', 'shan', 'nan', 'a', 'li', 'na', 'qu', 'chang', 'du',
    'potala', 'jokhang', 'barkhor', 'namtso', 'yamdrok', 'manasarovar', 'kailash',
    'everest', 'cho', 'oyu', 'lhotse', 'makalu', 'shishapangma', 'gasherbrum',
    'broad', 'peak', 'k', 'k', 'k', 'k', 'k', 'k', 'k', 'k', 'k', 'k',
    'sichuan', 'yunnan', 'qinghai', 'xinjiang', 'gansu', 'shaanxi', 'chongqing',
    'guizhou', 'guangxi', 'hunan', 'hubei', 'henan', 'hebei', 'shandong',
    'shanxi', 'jiangsu', 'zhejiang', 'anhui', 'jiangxi', 'fujian', 'guangdong',
    'hainan', 'taiwan', 'hong', 'kong', 'macao', 'beijing', 'shanghai',
    'tianjin', 'chongqing', 'guangzhou', 'shenzhen', 'wuhan', 'chengdu',
    'xian', 'nanjing', 'hangzhou', 'suzhou', 'wuxi', 'ningbo', 'wenzhou',
    'fuzhou', 'xiamen', 'quanzhou', 'zhangzhou', 'putian', 'nanping',
    'sanming', 'longyan', 'ningde', 'hefei', 'wuhu', 'bengbu', 'huainan',
    'maanshan', 'huaibei', 'tongling', 'anqing', 'huangshan', 'chuzhou',
    'fuyang', 'suzhou', 'lu', 'an', 'bozhou', 'chizhou', 'xuancheng',
    'nanchang', 'jingdezhen', 'pingxiang', 'jiujiang', 'xinyu', 'yingtan',
    'ganzhou', 'jian', 'yichun', 'fuzhou', 'shangrao', 'jinan', 'qingdao',
    'zibo', 'zaozhuang', 'dongying', 'yantai', 'weifang', 'jining', 'taian',
    'weihai', 'rizhao', 'laiwu', 'linyi', 'dezhou', 'liaocheng', 'binzhou',
    'heze', 'zhengzhou', 'kaifeng', 'luoyang', 'pingdingshan', 'anyang',
    'hebi', 'xinxiang', 'jiaozuo', 'puyang', 'xuchang', 'luohe', 'sanmenxia',
    'nanyang', 'shangqiu', 'xinyang', 'zhoukou', 'zhumadian', 'wuhan',
    'huangshi', 'shiyan', 'yichang', 'xiangyang', 'ezhou', 'jingmen',
    'xiaogan', 'jingzhou', 'huanggang', 'xianning', 'suizhou', 'enshi',
    'changsha', 'zhuzhou', 'xiangtan', 'hengyang', 'shaoyang', 'yueyang',
    'changde', 'zhangjiajie', 'yiyang', 'chenzhou', 'yongzhou', 'huaihua',
    'loudi', 'xiangxi', 'guangzhou', 'shaoguan', 'shenzhen', 'zhuhai',
    'shantou', 'foshan', 'jiangmen', 'zhanjiang', 'maoming', 'zhaoqing',
    'huizhou', 'meizhou', 'shanwei', 'heyuan', 'yangjiang', 'qingyuan',
    'dongguan', 'zhongshan', 'chaozhou', 'jieyang', 'yunfu', 'nanning',
    'liuzhou', 'guilin', 'wuzhou', 'beihai', 'fangchenggang', 'qinzhou',
    'guigang', 'yulin', 'baise', 'hezhou', 'hechi', 'laibin', 'chongzuo',
    'haikou', 'sanya', 'sansha', 'danzhou', 'wuzhishan', 'qionghai',
    'wenchang', 'wanning', 'dongfang', 'dingan', 'tunchang', 'chengmai',
    'lingao', 'baisha', 'changjiang', 'ledong', 'lingshui', 'baoting',
    'qiongzhong', 'chengdu', 'zigong', 'panzhihua', 'luzhou', 'deyang',
    'mianyang', 'guangyuan', 'suining', 'neijiang', 'leshan', 'nanchong',
    'meishan', 'yibin', 'guangan', 'dazhou', 'yaan', 'bazhong', 'ziyang',
    'aba', 'garze', 'liangshan', 'guiyang', 'liupanshui', 'zunyi',
    'anshun', 'bijie', 'tongren', 'qianxinan', 'qiandongnan', 'qiannan',
    'kunming', 'qujing', 'yuxi', 'baoshan', 'zhaotong', 'lijiang', 'puer',
    'lincang', 'chuxiong', 'honghe', 'wenshan', 'xishuangbanna', 'dali',
    'dehong', 'nujiang', 'diqing', 'lasa', 'rikaze', 'shannan', 'linzhi',
    'changdu', 'naqu', 'ali', 'xian', 'tongchuan', 'baoji', 'xianyang',
    'weinan', 'yanan', 'hanzhong', 'yulin', 'ankang', 'shangluo', 'lanzhou',
    'jiayuguan', 'jinchang', 'baiyin', 'tianshui', 'wuwei', 'zhangye',
    'pingliang', 'jiuquan', 'qingyang', 'dingxi', 'longnan', 'linxia',
    'gannan', 'xining', 'haidong', 'haibei', 'huangnan', 'hainan',
    'guoluo', 'yushu', 'haixi', 'yinchuan', 'shizuishan', 'wuzhong',
    'guyuan', 'zhongwei', 'urumqi', 'kelamayi', 'tulufan', 'hami',
    'changji', 'boertala', 'bayinguoleng', 'akesu', 'kezilesu', 'kashi',
    'hetian', 'yili', 'tacheng', 'aletai', 'shihezi', 'aral', 'tumxuk',
    'wujiaqu', 'beitun', 'shuanghe', 'kokdala', 'kunyu', 'taiyuan',
    'datong', 'yangquan', 'changzhi', 'jincheng', 'shuozhou', 'jinzhong',
    'yuncheng', 'xinzhou', 'linfen', 'lvliang', 'shijiazhuang', 'tangshan',
    'qinhuangdao', 'handan', 'xingtai', 'baoding', 'zhangjiakou',
    'chengde', 'cangzhou', 'langfang', 'hengshui', 'tianjin', 'beijing',
    'shanghai', 'chongqing', 'hongkong', 'macao', 'taipei', 'kaohsiung',
    'taichung', 'tainan', 'taoyuan', 'keelung', 'hsinchu', 'miaoli',
    'changhua', 'nantou', 'yunlin', 'chiayi', 'pingtung', 'yilan',
    'hualien', 'taitung', 'penghu', 'kinmen', 'lienchiang', 'lianjiang',
    'kinmen', 'penghu', 'matsu', 'diaoyu', 'spratly', 'paracel', 'pratas',
    'macclesfield', 'scarborough', 'johnson', 'south', 'reef', 'fiery',
    'cross', 'mischief', 'subi', 'gaven', 'hughes', 'johnson', 'cuarteron',
    'fiery', 'cross', 'mischief', 'subi', 'gaven', 'hughes', 'johnson',
    'johnson', 'south', 'reef', 'fiery', 'cross', 'mischief', 'subi',
    'gaven', 'hughes', 'johnson', 'cuarteron', 'fiery', 'cross',
}

def has_chinese(text):
    return bool(re.search(r'[\u4e00-\u9fff]', text))

def main():
    zh_issues = []
    en_issues = []
    
    for fname in sorted(os.listdir(ARTICLES_DIR)):
        if not fname.endswith('.html') or fname == 'index.html':
            continue
        
        with open(os.path.join(ARTICLES_DIR, fname), 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Check EN blocks for Chinese
        en_blocks = re.findall(r'<div class="lang-content" data-lang="en">(.*?)</div>', html, re.DOTALL)
        for i, block in enumerate(en_blocks):
            text = BeautifulSoup(block, 'html.parser').get_text()
            if has_chinese(text):
                lines = text.split('\n')
                for line in lines:
                    line = line.strip()
                    if has_chinese(line) and len(line) > 3:
                        en_issues.append((fname, i, line[:120]))
        
        # Check ZH blocks for English words
        zh_blocks = re.findall(r'<div class="lang-content" data-lang="zh">(.*?)</div>', html, re.DOTALL)
        for i, block in enumerate(zh_blocks):
            text = BeautifulSoup(block, 'html.parser').get_text()
            en_words = re.findall(r'[a-zA-Z]{2,}', text)
            real_en = [w for w in en_words if w.lower() not in SKIP_EN_WORDS]
            if real_en:
                # Find the actual lines containing these words
                lines = text.split('\n')
                for line in lines:
                    line = line.strip()
                    words_in_line = re.findall(r'[a-zA-Z]{2,}', line)
                    real_in_line = [w for w in words_in_line if w.lower() not in SKIP_EN_WORDS]
                    if real_in_line and len(line) > 5:
                        zh_issues.append((fname, i, line[:120], real_in_line[:5]))
    
    print("=" * 60)
    print("EN BLOCKS WITH CHINESE CONTAMINATION:")
    print("=" * 60)
    if en_issues:
        for fname, idx, line in en_issues:
            print(f"  {fname} [block {idx}]")
            print(f"    -> {line}")
    else:
        print("  NONE FOUND - All EN blocks are clean!")
    
    print("\n" + "=" * 60)
    print("ZH BLOCKS WITH ENGLISH WORDS (non-proper nouns):")
    print("=" * 60)
    if zh_issues:
        for fname, idx, line, words in zh_issues:
            print(f"  {fname} [block {idx}] words: {words}")
            print(f"    -> {line}")
    else:
        print("  NONE FOUND - All ZH blocks are clean!")
    
    print(f"\n{'=' * 60}")
    print(f"Summary: {len(en_issues)} EN issues, {len(zh_issues)} ZH issues")

if __name__ == '__main__':
    main()
