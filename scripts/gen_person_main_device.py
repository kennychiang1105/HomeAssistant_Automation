#!/usr/bin/env python3
"""Generate packages/v41_person_main_device.yaml and Automations/00-2S家人主要裝置切換AI.yaml (single source: CAND)."""
import yaml

H = '/homeassistant'
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
     '# 選項與裝置的對照在 Automations/00-2S 的 variables（兩邊由 scripts/gen_person_main_device.py 一起產生，不要手改）。',
     '# sensor.person_<id>_source_device：顯示 person.<id> 目前實際參考的裝置（person 的 source 屬性）、該裝置狀態與 person 的追蹤裝置清單。',
     '# ────────────────────────────────────────────────────────',
     'input_select:']
for pid, (name, opts) in CAND.items():
    P += ['  person_main_device_%s:' % pid,
          '    name: "%s 的主要裝置（person.%s 參考）"' % (name, pid),
          '    icon: mdi:cellphone-check',
          '    options:']
    P += ['      - "%s"' % lb for lb, _ in opts]
P += ['input_boolean:',
      '  person_main_device_busy:',
      '    name: 家人主要裝置切換中（內部）',
      '    icon: mdi:progress-wrench',
      '    initial: false',
      'shell_command:',
      "  person_set_main: \"python3 /config/scripts/person_set_main.py {{ pid }} {{ entity }} '{{ label }}'\"",
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
A = '''# ──────────────────────────────────────────────
# 00-2S家人主要裝置切換AI (V4.2.0)
# 更新紀錄：
# - V4.2.0（2026-10-22）：新增。自動化管理面板可選每位家人（Kenny／Iris／Jerry／Elay）的主要裝置（person.* 參考的 device_tracker）。
#   選單改變 → 檢查「選的裝置在不在家」要和 person 目前的在不在家一致（不一致就退回原選項並發 HA 通知，避免切換後 person 突然變離家而觸發離家情境）
#   → 改寫 packages/persons.yaml（scripts/person_set_main.py，舊檔存 persons.yaml.bak）→ person.reload → 驗證 person 的 source 已是新裝置，發 HA 資訊通知。
#   HA 啟動後 60 秒把四個選單對齊 person 實際參考的裝置（只改選單，不改 persons.yaml）。
#   選項與裝置對照由 scripts/gen_person_main_device.py 與 packages/v41_person_main_device.yaml 一起產生。
# ──────────────────────────────────────────────
- id: ai_00_2s_person_main_device
  alias: 00-2S家人主要裝置切換AI (V4.2.0)
  description: 面板選家人的主要裝置 → 檢查 → 改 persons.yaml → person.reload → 驗證
  mode: queued
  max: 6
  max_exceeded: silent
  triggers:
    - trigger: state
      id: select
      entity_id:
%s
      not_from:
        - unavailable
        - unknown
    - trigger: homeassistant
      id: ha_start
      event: start
  variables:
    automation_version: "V4.2.0"
    pmap: %s
    pname: %s
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
                      src: "{{ state_attr('person.' ~ repeat.item, 'source') }}"
                      lab: >-
                        {%% set ns = namespace(l='') %%}{%% for k, v in pmap[repeat.item].items() %%}{%% if v == src %%}{%% set ns.l = k %%}{%% endif %%}{%% endfor %%}{{ ns.l }}
                  - if: "{{ lab != '' and states('input_select.person_main_device_' ~ repeat.item) != lab }}"
                    then:
                      - action: input_select.select_option
                        target:
                          entity_id: "input_select.person_main_device_{{ repeat.item }}"
                        data:
                          option: "{{ lab }}"
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
            pid: "{{ trigger.entity_id.split('person_main_device_')[1] }}"
            label: "{{ trigger.to_state.state }}"
            ent: "{{ pmap[pid].get(label, '') }}"
            p_state: "{{ states('person.' ~ pid) }}"
            c_state: "{{ states(ent) if ent else 'unknown' }}"
            ok_guard: "{{ ent != '' and c_state not in ['unknown', 'unavailable'] and ((c_state == 'home') == (p_state == 'home')) }}"
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
                    label: "{{ label }}"
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
                          {%% if now_src == ent %%}已改為「{{ label }}」，person.{{ pid }} 現在參考 {{ ent }}。{%% else %%}已改寫設定，但 person.{{ pid }} 目前參考的是 {{ now_src }}，請檢查 persons.yaml。{%% endif %%}
                  else:
                    - action: input_select.select_option
                      target:
                        entity_id: "{{ trigger.entity_id }}"
                      data:
                        option: "{{ trigger.from_state.state }}"
                    - action: script.notify_dispatch
                      data:
                        level: important
                        line: false
                        source: "00-2S家人主要裝置切換AI (V4.2.0)"
                        version: "{{ automation_version }}"
                        title: "{{ pname[pid] }} 的主要裝置沒有切換"
                        message: "改寫 persons.yaml 失敗：{{ (res.stdout | default('') ~ ' ' ~ res.stderr | default('')) | trim if res is mapping else '無回應' }}。已退回「{{ trigger.from_state.state }}」。"
          default:
            - action: input_select.select_option
              target:
                entity_id: "{{ trigger.entity_id }}"
              data:
                option: "{{ trigger.from_state.state }}"
            - action: script.notify_dispatch
              data:
                level: info
                line: false
                source: "00-2S家人主要裝置切換AI (V4.2.0)"
                version: "{{ automation_version }}"
                title: "{{ pname[pid] }} 的主要裝置沒有切換"
                message: >-
                  「{{ label }}」目前{{ '不在家' if c_state != 'home' else '在家' }}，但 {{ pname[pid] }} 目前{{ '在家' if p_state == 'home' else '不在家' }}。為避免切換後在家狀態突然改變、誤觸發離家／到家情境，已退回「{{ trigger.from_state.state }}」。請等該裝置的在家狀態和 {{ pname[pid] }} 一致再切換。
        - delay: "00:00:02"
        - action: input_boolean.turn_off
          target:
            entity_id: input_boolean.person_main_device_busy
''' % ('\n'.join('        - ' + e for e in sel_ents), yaml.safe_dump(mp, allow_unicode=True, default_flow_style=True, width=10000).strip().replace('\n', ' '), yaml.safe_dump(names, allow_unicode=True, default_flow_style=True, width=10000).strip().replace('\n', ' '))
A = A.replace('%%', '%')
yaml.safe_load(A)
open(H + '/Automations/00-2S家人主要裝置切換AI.yaml', 'w', encoding='utf-8').write(A)
print('generated', len(P), 'package lines;', len(A.split('\n')), 'automation lines')




