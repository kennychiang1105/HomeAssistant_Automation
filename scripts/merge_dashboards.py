import yaml
class Inc(str): pass
class L(yaml.SafeLoader): pass
L.add_constructor('!include', lambda l,n: Inc('!include '+l.construct_scalar(n)))
yaml.add_representer(Inc, lambda d,x: d.represent_scalar('!include', str(x)[len('!include '):], style="'"))
land=yaml.load(open('ui/land.yaml'),L); port=yaml.load(open('ui/port.yaml'),L)
lv={v['path']:v for v in land['views']}; pv={v['path']:v for v in port['views']}
def cond(media, card):
    return {'type':'conditional','conditions':[{'condition':'screen','media_query':media}],'card':card}
def strip_layout(c):
    c=dict(c); c.pop('view_layout',None); return c
# 家：橫向＝左側選單＋3D 地圖；直向＝直向地圖＋人員＋按鈕…
# 全面採用 Home Assistant 2026.10 原生卡片級 visibility 屬性
lh=lv['home']; ph=pv['home']
land_card={'type':'custom:layout-card','visibility':[{'condition':'screen','media_query':'(orientation: landscape)'}],'layout_type':'custom:grid-layout','layout':lh['layout'],'cards':lh['cards']}
port_card={'type':'vertical-stack','visibility':[{'condition':'screen','media_query':'(orientation: portrait)'}],'cards':ph['cards']}
home={'title':'家','path':'home','icon':lh['icon'],'type':'custom:grid-layout','layout':{'grid-template-columns':'minmax(0, 1fr)','grid-gap':'0px','margin':'0 auto'},
      'cards':[land_card, port_card]}
views=[home]
for k in ['scenes','all','floor-1f','floor-2f','floor-stairs','system']:
    views.append(lv[k])
out={'button_card_templates':land['button_card_templates'],'title':'智慧家庭','views':views}
txt="# 智慧家庭（橫向＋直向合併版，V4.1.0 現代化原生 Visibility 版）：「家」頁依螢幕方向切換（橫向＝左側選單＋3D 地圖；直向＝直向地圖＋人員＋按鈕），\n# 其餘頁面兩種方向內容相同。全面採用 Home Assistant 2026.10 原生卡片級 visibility 屬性，淘汰冗餘 nested conditional 容器。\n"
txt+=yaml.dump(out,allow_unicode=True,sort_keys=False,width=200)
open('ui/smart-home.yaml','w').write(txt)
print(len(txt.splitlines()),'lines'); 
back=yaml.load(txt,L); print('reload ok', [v['path'] for v in back['views']])
