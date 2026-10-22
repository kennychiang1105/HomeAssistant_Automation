#!/usr/bin/env python3
"""Generate packages/v41_person_main_device.yaml and Automations/00-2S家人主要裝置切換AI.yaml (single source: CAND / OTHER).

Run on the HA host after editing the candidate list:   python3 scripts/gen_person_main_device.py
then reload: input_select, input_text, template, automation (check_config first).
"""
import yaml

H = '/homeassistant'
OTHER = '其他（自訂，在下方欄位輸入 device_tracker）'
# person id -> (display name, [(label, device_tracker entity)]); the first option is the device in packages/persons.yaml today
CAND = {
    'kenny': ('Kenny', [
        ('iPhone 17 Pro Max（路由器）', 'device_tracker.iphone_17_pro_max_kenny'),
        ('iPhone 17 Pro Max（App GPS）', 'device_tracker.iphone_17_pro_max_kenny_2'),
        ('iPad Pro 2024（路由器）', 'device_tracker.ipad_pro_2024_kenny'),
        ('iPad mini（App GPS）', 'device_tracker.jiang_zi_yang_de_ipad'),
        ('Apple Watch Ultra 3（路由器）', 'device_tracker.apple_watch_ultra_3_kenny'),
    ]),
    'iris': ('Iris', [
        ('iPhone 13 Pro Max（路由器）', 'device_tracker.iphone13promaxiris'),
    ]),
    'jerry': ('Jerry', [
        ('iPhone 16（路由器）', 'device_tracker.iphone_16_jerry'),
        ('Redmi Note 11 Pro 5G（路由器）', 'device_tracker.redmi_note_11_pro_5g'),
        ('iPhone Xr（路由器）', 'device_tracker.iphone_xr_jerry'),
        ('iPad Pro 2021（路由器）', 'device_tracker.ipad_pro_2021_jerry'),
    ]),
    'elay': ('Elay', [
        ('iPhone 16 Pro Max（路由器）', 'device_tracker.unifi_16_cc_a1_4d_4f_42_default'),
        ('iPhone 13 Pro（路由器）', 'device_tracker.unifi_16_cc_a1_4d_4f_42_old'),
        ('iPad Air 5（路由器）', 'device_tracker.ipad_air_5_elay'),
    ]),
}

# ---------------- package ----------------
P = ['# ────────────────────────────────────────────────────────',
     '# 家人主要裝置選擇（V4.2.0，2026-10-22）',
     '# person.kenny／iris／jerry／elay 是 YAML 定義（packages/persons.yaml），在不在家都由它的 device_trackers 決定，at_home_* 等判斷也都讀它。',
     '# 這裡讓「自動化管理面板」可以選每個人的主要裝置：選單改變 → 00-2S家人主要裝置切換AI 先檢查（選的裝置在不在家要和 person 目前一致，',
     '# 免得切換後 person 突然變離家觸發離家情境）→ 改寫 persons.yaml（scripts/person_set_main.py，舊檔存 persons.yaml.bak）→ person.reload。',
     '# 選單最後一項「其他（自訂）」：到下面的文字欄位輸入 device_tracker.xxx（小寫英數底線），就能用清單以外的裝置；選「其他」後再改文字欄位也會重新套用。',
     '# 選項與裝置的對照在 Automations/00-2S 的 variables（兩邊由 scripts/gen_person_main_device.py 一起產生，不要手改）。',
     '# sensor.person_<id>_source_device：顯示 person.<id> 目前實際參考的裝置（person 的 source 屬性）、該裝置狀態與 person 的追蹤裝置清單。',
     '# ────────────────────────────────────────────────────────',
     'input_select:']
for pid, (name, opts) in CAND.items():
    P += ['  person_main_device_%s:' % pid,
          '    name: "%s 的主要裝置（person.%s 參考）"' % (name, pid),
          '    icon: mdi:cellphone-check',
          '    options:']
    P += ['      - "%s"' % lb for lb, _ in opts] + ['      - "%s"' % OTHER]
P += ['input_text:']
for pid, (name, opts) in CAND.items():
    P += ['  person_main_device_custom_%s:' % pid,
          '    name: "%s 的自訂裝置（選「其他」時使用，例：device_tracker.xxx）"' % name,
          '    icon: mdi:cellphone-edit',
          '    max: 100',
          '    pattern: "^(device_tracker[.][a-z0-9_]+)?$"',
          '    initial: ""']
P += ['input_boolean:',
      '  person_main_device_busy:',
      '    name: 家人主要裝置切換中（內部）',
      '    icon: mdi:progress-wrench',
      '    initial: false',
      'shell_command:',
      "  person_set_main: \"python3 /config/scripts/person_set_main.py '{{ pid }}' '{{ entity }}' '{{ label }}'\"",
      'template:',
      '  - sensor:']
for pid, (name, opts) in CAND.items():
    s = "state_attr('person.%s','source')" % pid
    P += ['      - name: person_%s_source_device' % pid,
          '        unique_id: person_%s_source_device' % pid,
          '        icon: mdi:cellphone-link',
          '        state: >-',
          '          {%% set s = %s %%}{%% set n = (state_attr(s, \'friendly_name\') | default(s, true) | string) if s else \'\' %%}' % s,
          '          {% set h = (n | length) // 2 %}',
          "          {{ '未參考任何裝置' if not s else (n[:h] | trim if (n | length) % 2 == 1 and n[:h] | trim == n[h + 1:] | trim else n) }}",
          '        attributes:',
          '          person_name: "%s"' % name,
          '          person_state: "{{ states(\'person.%s\') }}"' % pid,
          '          source_entity: "{{ %s or \'\' }}"' % s,
          '          source_state: "{{ states(%s) if %s else \'unknown\' }}"' % (s, s),
          '          trackers: "{{ state_attr(\'person.%s\',\'device_trackers\') | default([], true) | join(\'、\') }}"' % pid]
open(H + '/packages/v41_person_main_device.yaml', 'w', encoding='utf-8').write('\n'.join(P) + '\n')
yaml.safe_load(open(H + '/packages/v41_person_main_device.yaml', encoding='utf-8').read())

# ---------------- automation ----------------
mp = {pid: {lb: ent for lb, ent in opts} for pid, (_, opts) in CAND.items()}
names = {pid: nm for pid, (nm, _) in CAND.items()}
sel_ents = ['input_select.person_main_device_%s' % pid for pid in CAND]
txt_ents = ['input_text.person_main_device_custom_%s' % pid for pid in CAND]
flow = lambda d: yaml.safe_dump(d, allow_unicode=True, default_flow_style=True, width=10000).strip().replace('\n', ' ')
A = r'''# ──────────────────────────────────────────────
# 00-2S家人主要裝置切換AI (V4.2.0)
# 更新紀錄：
# - V4.2.0（2026-10-22）：新增。自動化管理面板可選每位家人（Kenny／Iris／Jerry／Elay）的主要裝置（person.* 參考的 device_tracker）。
#   選單改變 → 檢查「選的裝置在不在家」要和 person 目前的在不在家一致（不一致就退回原選項並發 HA 通知，避免切換後 person 突然變離家而觸發離家情境）
#   → 改寫 packages/persons.yaml（scripts/person_set_main.py，舊檔存 persons.yaml.bak）→ person.reload → 驗證 person 的 source 已是新裝置，發 HA 資訊通知。
#   選單最後一項「其他（自訂）」：選了才會出現該家人的文字欄位，輸入 device_tracker.xxx（小寫英數底線）後套用；欄位還是空的時只停在「其他」，不退回也不通知；選了「其他」之後改文字欄位也會重新套用。
#   HA 啟動後 60 秒把四個選單對齊 person 實際參考的裝置（不在清單內就選「其他」並把裝置填進文字欄位；只改選單，不改 persons.yaml）。
#   選項與裝置對照由 scripts/gen_person_main_device.py 與 packages/v41_person_main_device.yaml 一起產生。
# ──────────────────────────────────────────────
- id: ai_00_2s_person_main_device
  alias: 00-2S家人主要裝置切換AI (V4.2.0)
  description: 面板選家人的主要裝置 → 檢查 → 改 persons.yaml → person.reload → 驗證
  mode: queued
  max: 8
  max_exceeded: silent
  triggers:
    - trigger: state
      id: select
      entity_id:
@SEL@
      not_from:
        - unavailable
        - unknown
    - trigger: state
      id: custom
      entity_id:
@TXT@
      not_from:
        - unavailable
        - unknown
    - trigger: homeassistant
      id: ha_start
      event: start
  variables:
    automation_version: "V4.2.0"
    other_label: "@OTHER@"
    pmap: @PMAP@
    pname: @PNAME@
  actions:
    - choose:
        # ── HA 啟動：選單對齊 person 實際參考的裝置 ──
        - conditions:
            - condition: trigger
              id: ha_start
          sequence:
            - delay: "00:01:00"
            - action: input_boolean.turn_on
              target:
                entity_id: input_boolean.person_main_device_busy
            - repeat:
                for_each: "{{ pmap.keys() | list }}"
                sequence:
                  - variables:
                      src: "{{ state_attr('person.' ~ repeat.item, 'source') or '' }}"
                      lab: >-
                        {% set ns = namespace(l='') %}{% for k, v in pmap[repeat.item].items() %}{% if v == src %}{% set ns.l = k %}{% endif %}{% endfor %}{{ ns.l }}
                  - choose:
                      - conditions:
                          - condition: template
                            value_template: "{{ lab != '' and states('input_select.person_main_device_' ~ repeat.item) != lab }}"
                        sequence:
                          - action: input_select.select_option
                            target:
                              entity_id: "input_select.person_main_device_{{ repeat.item }}"
                            data:
                              option: "{{ lab }}"
                      - conditions:
                          - condition: template
                            value_template: "{{ lab == '' and src.startswith('device_tracker.') }}"
                        sequence:
                          - action: input_text.set_value
                            target:
                              entity_id: "input_text.person_main_device_custom_{{ repeat.item }}"
                            data:
                              value: "{{ src }}"
                          - action: input_select.select_option
                            target:
                              entity_id: "input_select.person_main_device_{{ repeat.item }}"
                            data:
                              option: "{{ other_label }}"
            - delay: "00:00:02"
            - action: input_boolean.turn_off
              target:
                entity_id: input_boolean.person_main_device_busy
      default:
        - condition: template
          value_template: "{{ trigger.from_state is not none and trigger.from_state.state != trigger.to_state.state }}"
        - condition: state
          entity_id: input_boolean.person_main_device_busy
          state: "off"
        - variables:
            is_txt: "{{ trigger.id == 'custom' }}"
            pid: "{{ trigger.entity_id.split('person_main_device_custom_')[1] if trigger.id == 'custom' else trigger.entity_id.split('person_main_device_')[1] }}"
            label: "{{ states('input_select.person_main_device_' ~ pid) if trigger.id == 'custom' else trigger.to_state.state }}"
            custom_ent: "{{ (trigger.to_state.state if trigger.id == 'custom' else states('input_text.person_main_device_custom_' ~ pid)) | trim | lower }}"
            custom_ok: "{{ custom_ent | regex_match('^device_tracker[.][a-z0-9_]+$') }}"
            ent: "{{ (custom_ent if custom_ok else '') if label == other_label else pmap[pid].get(label, '') }}"
            p_state: "{{ states('person.' ~ pid) }}"
            c_state: "{{ states(ent) if ent else 'unknown' }}"
            ok_guard: "{{ ent != '' and c_state not in ['unknown', 'unavailable'] and ((c_state == 'home') == (p_state == 'home')) }}"
            back_opt: "{{ trigger.from_state.state }}"
        # 文字欄位改變時，只有選單目前是「其他」才套用
        - condition: template
          value_template: "{{ trigger.id != 'custom' or label == other_label }}"
        # 「其他」但文字欄位是空的或格式不對：先停在「其他」讓輸入欄出現，等輸入有效的 device_tracker 再套用（不退回、不通知）
        - condition: template
          value_template: "{{ not (label == other_label and not custom_ok) }}"
        # 選單已經是 person 目前參考的裝置（例如退回選項、重複選同一個）就不用處理
        - condition: template
          value_template: "{{ ent != state_attr('person.' ~ pid, 'source') }}"
        - action: input_boolean.turn_on
          target:
            entity_id: input_boolean.person_main_device_busy
        - choose:
            - conditions:
                - condition: template
                  value_template: "{{ ok_guard }}"
              sequence:
                - action: shell_command.person_set_main
                  data:
                    pid: "{{ pid }}"
                    entity: "{{ ent }}"
                    label: "{{ label if label != other_label else '自訂' }}"
                  response_variable: res
                - if: "{{ res is mapping and res.returncode == 0 and (res.stdout | trim).startswith('OK') }}"
                  then:
                    - action: person.reload
                    - delay: "00:00:03"
                    - variables:
                        now_src: "{{ state_attr('person.' ~ pid, 'source') }}"
                    - action: script.notify_dispatch
                      data:
                        level: "{{ 'info' if now_src == ent else 'important' }}"
                        line: false
                        source: "00-2S家人主要裝置切換AI (V4.2.0)"
                        version: "{{ automation_version }}"
                        title: "{{ pname[pid] }} 的主要裝置"
                        message: >-
                          {% if now_src == ent %}已改為「{{ label if label != other_label else ent }}」，person.{{ pid }} 現在參考 {{ ent }}。{% else %}已改寫設定，但 person.{{ pid }} 目前參考的是 {{ now_src }}，請檢查 persons.yaml。{% endif %}
                  else:
                    - choose:
                        - conditions:
                            - condition: template
                              value_template: "{{ is_txt }}"
                          sequence:
                            - action: input_text.set_value
                              target:
                                entity_id: "{{ trigger.entity_id }}"
                              data:
                                value: "{{ back_opt }}"
                      default:
                        - action: input_select.select_option
                          target:
                            entity_id: "{{ trigger.entity_id }}"
                          data:
                            option: "{{ back_opt }}"
                    - action: script.notify_dispatch
                      data:
                        level: important
                        line: false
                        source: "00-2S家人主要裝置切換AI (V4.2.0)"
                        version: "{{ automation_version }}"
                        title: "{{ pname[pid] }} 的主要裝置沒有切換"
                        message: "改寫 persons.yaml 失敗：{{ (res.stdout | default('') ~ ' ' ~ res.stderr | default('')) | trim if res is mapping else '無回應' }}。已退回原設定。"
          default:
            - choose:
                - conditions:
                    - condition: template
                      value_template: "{{ is_txt }}"
                  sequence:
                    - action: input_text.set_value
                      target:
                        entity_id: "{{ trigger.entity_id }}"
                      data:
                        value: "{{ back_opt }}"
              default:
                - action: input_select.select_option
                  target:
                    entity_id: "{{ trigger.entity_id }}"
                  data:
                    option: "{{ back_opt }}"
            - action: script.notify_dispatch
              data:
                level: info
                line: false
                source: "00-2S家人主要裝置切換AI (V4.2.0)"
                version: "{{ automation_version }}"
                title: "{{ pname[pid] }} 的主要裝置沒有切換"
                message: >-
                  {% if label == other_label and not custom_ok %}請先在「{{ pname[pid] }} 的自訂裝置」欄位輸入有效的 device_tracker.xxx（小寫英數底線），再選「其他」。已退回原設定。
                  {% elif c_state in ['unknown', 'unavailable'] %}找不到裝置 {{ ent }} 的狀態（不存在或離線），已退回原設定。
                  {% else %}「{{ label if label != other_label else ent }}」目前{{ '不在家' if c_state != 'home' else '在家' }}，但 {{ pname[pid] }} 目前{{ '在家' if p_state == 'home' else '不在家' }}。為避免切換後在家狀態突然改變、誤觸發離家／到家情境，已退回原設定。請等該裝置的在家狀態和 {{ pname[pid] }} 一致再切換。{% endif %}
        - delay: "00:00:02"
        - action: input_boolean.turn_off
          target:
            entity_id: input_boolean.person_main_device_busy
'''
A = (A.replace('@SEL@', '\n'.join('        - ' + e for e in sel_ents))
      .replace('@TXT@', '\n'.join('        - ' + e for e in txt_ents))
      .replace('@OTHER@', OTHER).replace('@PMAP@', flow(mp)).replace('@PNAME@', flow(names)))
yaml.safe_load(A)
open(H + '/Automations/00-2S家人主要裝置切換AI.yaml', 'w', encoding='utf-8').write(A)
print('generated', len(P), 'package lines;', len(A.split('\n')), 'automation lines')

