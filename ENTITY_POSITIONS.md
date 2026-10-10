# 實體位置對照表 (ENTITY_POSITIONS)

> 由 `scripts/generate_floorplan_v4.py positions` 自動產生。來源：平面圖 SVG 實體圖層 + 使用者在 3D 卡片「✎ 調整位置」存下的修正（`來源=調整`）。
> 座標：每層平面圖像素，原點在左上角，x 向東、y 向南。3D 世界座標 = 平面座標 − 樓層尺寸/2。

樓層尺寸：1F 818×519、2F 995×605、3F 802×519、4F 846×519、5F 801×519

## 1F

| 區域 | 名稱 | 實體 | 類型 | x | y | 燈群組 | 來源 |
|---|---|---|---|---|---|---|---|
| 1F | 車庫攝影機 High resolution channel | `camera.g6_instant_high_resolution_channel` | camera | 387.95 | 29.42 |  | 原圖 |
| 車庫 | U6 Mesh (1F) 狀態 | `sensor.u6_mesh_1f_state` | ap | 422.2 | 426.5 |  | 原圖 |
| 車庫 | Tesla充電樁 | `sensor.tesla_charger_homekit_status` | charger | 470.6 | 426.5 |  | 原圖 |
| 車庫 | sensor.tesla_wall_connector_status1 | `sensor.tesla_wall_connector_status1` | charger | 483.2 | 426.5 |  | 原圖 ⚠HA無此實體 |
| 車庫 | 車庫鐵門 | `cover.garage` | cover | 13.0 | 212.8 |  | 原圖 |
| 車庫 | 車庫攝影機 動作 | `binary_sensor.g6_instant_motion` | motion | 403.5 | 37.0 |  | 原圖 |
| 車庫 | 車庫攝影機 偵測到人員 | `binary_sensor.che_ku_she_ying_ji_person_detected` | person | 423.5 | 37.0 |  | 原圖 |
| 車庫 | 車庫主燈 | `switch.che_ku_zhu_deng` | switch | 311.0 | 184.2 |  | 原圖 |
| 車庫 | 車庫樓梯燈 | `switch.lou_ti_deng` | switch | 383.5 | 473.0 |  | 原圖 |
| 車庫 | 車庫鐵門溫度 | `sensor.garage_temperature` | temp | 13.0 | 330.4 |  | 原圖 |

## 2F

| 區域 | 名稱 | 實體 | 類型 | x | y | 燈群組 | 來源 |
|---|---|---|---|---|---|---|---|
| 2F | 廁所小米人體傳感器 Motion | `binary_sensor.e406bf25caa1_motion` | motion | 855.39 | 441.69 |  | 原圖 |
| 客廳 | U6-Pro (2F) 狀態 | `sensor.u6_pro_2f_state` | ap | 433.3 | 58.0 |  | 原圖 |
| 客廳 | UDMSE(Kenny) 狀態 | `sensor.udmse_kenny_state` | ap | 438.3 | 39.4 |  | 原圖 |
| 客廳 | 二樓門鎖 | `input_boolean.er_lou_men_suo_tong_bu_kai_guan` | doorlock | 177 | 87.0 |  | 原圖 |
| 客廳 | 客廳電風扇 | `fan.ke_ting_dian_feng_shan` | fan | 243.0 | 221.3 |  | 原圖 |
| 客廳 | 空氣清淨機 | `fan.kong_qi_qing_jing_ji` | fan | 459.5 | 113.9 |  | 原圖 |
| 客廳 | 客廳濕度(Homepod) | `sensor.livingroom_homepodmini_humidity` | hum | 300.0 | 222.0 |  | 原圖 |
| 客廳 | 空氣清淨機 濕度 | `sensor.kong_qi_qing_jing_ji_humidity` | hum | 487.7 | 114.5 |  | 原圖 |
| 客廳 | 客廳小燈 灯 | `light.yeelink_color5_4181_light` | light | 352.4 | 298.0 | 2f_客廳_lights_1 | 原圖 |
| 客廳 | 客廳燈組2 | `light.ke_ting_deng_zu_2` | light | 352.4 | 313.0 | 2f_客廳_lights_1 | 原圖 |
| 客廳 | 客廳燈組1 | `light.ke_ting_deng_zu_1_ha` | light | 369.0 | 313.0 | 2f_客廳_lights_1 | 原圖 |
| 客廳 | 客廳燈組3 | `light.ke_ting_deng_zu_3` | light | 369.0 | 298.0 | 2f_客廳_lights_1 | 原圖 |
| 客廳 | 客廳電視 | `media_player.ke_ting_dian_shi` | media_player | 363.0 | 23.0 |  | 原圖 |
| 客廳 | 客廳Homepod | `media_player.ke_ting_homepod` | media_player | 497.7 | 477.8 |  | 原圖 |
| 客廳 | 餐廳Homepod插座 | `switch.can_ting_homepodcha_zuo` | plug | 501.8 | 495.0 |  | 原圖 |
| 客廳 | 路燈 | `switch.lu_deng` | switch | 167.6 | 459.4 | 2f_客廳_lights_3 | 原圖 |
| 客廳 | 客廳環繞燈 | `switch.ke_ting_bi_deng` | switch | 196.3 | 174.8 |  | 原圖 |
| 客廳 | 客廳崁燈 | `switch.ke_ting_kan_deng` | switch | 238.0 | 489.2 | 2f_客廳_lights_3 | 原圖 |
| 客廳 | 客廳壁燈 | `switch.ke_ting_huan_rao_deng` | switch | 360.7 | 497.8 |  | 原圖 |
| 客廳 | 客廳溫度(Homepod) | `sensor.livingroom_homepodmini_temperature` | temp | 300.0 | 200.0 |  | 原圖 |
| 客廳 | 空氣清淨機 溫度 | `sensor.kong_qi_qing_jing_ji_temperature` | temp | 473.6 | 114.5 |  | 原圖 |
| 客廳 | 空氣清淨機 PM2.5 | `sensor.kong_qi_qing_jing_ji_pm2_5` | value | 501.8 | 114.5 |  | 原圖 |
| 廁所 | 車庫樓梯燈 | `switch.lou_ti_deng` | switch | 820.3 | 470.1 | 2f_廁所_lights_8 | 原圖 |
| 廁所 | 廁所燈 | `switch.ce_suo_deng` | switch | 911.4 | 446.1 | 2f_廁所_lights_8 | 原圖 |
| 廚房 | 廚房感測器 濕度 | `sensor.kitchenm_shi_du` | hum | 830.9 | 23.0 |  | 原圖 |
| 廚房 | 廚房環境感測器 廚房 濕度 | `sensor.chu_fang_chu_fang_huan_jing_gan_ce_qi_chu_fang_shi_du` | hum | 849.3 | 326.1 |  | 原圖 |
| 廚房 | 廚房感測器 佔空 | `binary_sensor.unknown_zhan_kong` | motion | 846.6 | 12.81 |  | 原圖 |
| 廚房 | 廚房小米人體傳感器 Motion | `binary_sensor.kitchen_motion` | motion | 948.82 | 239.47 |  | 原圖 |
| 廚房 | 廚房插座 Plug | `switch.0x00158d0003923796_plug` | plug | 892.9 | 22.1 |  | 原圖 |
| 廚房 | 廚房環境感測器 廚房一氧化碳危險 | `binary_sensor.chu_fang_chu_fang_huan_jing_gan_ce_qi_chu_fang_yi_yang_hua_tan_wei_xian` | safety | 836.8 | 342.1 |  | 原圖 |
| 廚房 | 廚房環境感測器 廚房甲醛危險 | `binary_sensor.chu_fang_chu_fang_huan_jing_gan_ce_qi_chu_fang_jia_quan_wei_xian` | safety | 849.3 | 342.1 |  | 原圖 |
| 廚房 | 廚房環境感測器 廚房空氣品質危險 | `binary_sensor.chu_fang_chu_fang_huan_jing_gan_ce_qi_chu_fang_kong_qi_pin_zhi_wei_xian` | safety | 862.6 | 342.1 |  | 原圖 |
| 廚房 | 廚房燈 | `switch.chu_fang_deng` | switch | 835.1 | 198.3 |  | 原圖 |
| 廚房 | 廚房感測器 溫度 | `sensor.kitchenm_wen_du` | temp | 815.3 | 23.0 |  | 原圖 |
| 廚房 | 廚房環境感測器 廚房 溫度 | `sensor.chu_fang_chu_fang_huan_jing_gan_ce_qi_chu_fang_wen_du` | temp | 836.0 | 326.1 |  | 原圖 |
| 廚房 | 廚房環境感測器 廚房 CO2 | `sensor.chu_fang_chu_fang_huan_jing_gan_ce_qi_chu_fang_co2` | value | 825.3 | 334.3 |  | 原圖 |
| 廚房 | 廚房環境感測器 廚房 一氧化碳 (CO) | `sensor.chu_fang_chu_fang_huan_jing_gan_ce_qi_chu_fang_yi_yang_hua_tan_co` | value | 862.6 | 326.1 |  | 原圖 |
| 玄關 | 門口燈 | `switch.men_kou_deng` | switch | 130.0 | 87.0 |  | 原圖 |
| 餐廳 | 餐廳燈組1 | `light.can_ting_deng_zu_1_ha` | light | 652.4 | 154.5 |  | 原圖 |
| 餐廳 | 餐廳崁燈 | `switch.can_ting_kan_deng` | switch | 544.2 | 63.4 |  | 原圖 |
| 餐廳 | 二三樓樓梯燈 | `switch.er_san_lou_lou_ti_deng` | switch | 582.5 | 480.1 |  | 原圖 |
| 餐廳 | 餐廳壁燈 | `switch.can_ting_bi_deng` | switch | 652.4 | 15.5 |  | 原圖 |

## 3F

| 區域 | 名稱 | 實體 | 類型 | x | y | 燈群組 | 來源 |
|---|---|---|---|---|---|---|---|
| 3F | Switch Lite 8 PoE (3F) 狀態 | `sensor.switch_lite_8_poe_state` | ap | 262.0 | 40.0 |  | 原圖 |
| 主臥 | U6-Lite (3F) 狀態 | `sensor.u6_lite_3f_state` | ap | 227.0 | 39.7 |  | 原圖 |
| 樓梯 | 三樓樓梯燈 | `switch.san_lou_lou_ti_deng` | switch | 372.5 | 405.4 |  | 原圖 |
| 樓梯 | 二三樓樓梯燈 | `switch.er_san_lou_lou_ti_deng` | switch | 581.0 | 354.5 | 3f_樓梯_lights_1 | 原圖 |
| 樓梯 | 三四樓樓梯燈 | `switch.san_si_lou_lou_ti_deng` | switch | 581.0 | 456.0 | 3f_樓梯_lights_1 | 原圖 |

## 4F

| 區域 | 名稱 | 實體 | 類型 | x | y | 燈群組 | 來源 |
|---|---|---|---|---|---|---|---|
| 前臥 | U6 Extender (4F Elay) 狀態 | `sensor.u6_extender_4f_elay_state` | ap | 80.7 | 196.7 |  | 原圖 |
| 後臥 | U6-IW (4F Jerry) 狀態 | `sensor.u6_iw_4f_jerry_state` | ap | 577.5 | 308.7 |  | 原圖 |
| 樓梯 | 四樓樓梯燈 灯 | `light.yeelink_color5_0fb7_light` | light | 388.3 | 418.5 |  | 原圖 |
| 樓梯 | 頂樓樓梯燈 灯 | `light.yeelink_color5_13b8_light` | light | 611.0 | 464.2 | 4f_樓梯_lights_1 | 原圖 |
| 樓梯 | 三四樓樓梯燈 | `switch.san_si_lou_lou_ti_deng` | switch | 611.5 | 380.7 | 4f_樓梯_lights_1 | 原圖 |

## 5F

| 區域 | 名稱 | 實體 | 類型 | x | y | 燈群組 | 來源 |
|---|---|---|---|---|---|---|---|
| 前陽台 | 陽台燈 | `switch.yang_tai_deng` | switch | 171.6 | 278 |  | 調整 |
| 房間 | U6-IW (5F Kenny) 狀態 | `sensor.u6_iw_5f_kenny_state` | ap | 459.0 | 359.4 |  | 原圖 |
| 房間 | 頂樓空調 | `climate.ding_lou_kong_diao` | climate | 318.5 | 16.0 |  | 原圖 |
| 房間 | 頂樓電風扇 小米智能變頻電風扇 2 Pro | `fan.dmaker_p33_eabd_fan` | fan | 335.3 | 359.4 |  | 原圖 |
| 房間 | 頂樓濕度(Homepod) | `sensor.5f_homepodmini_humidity` | hum | 430.5 | 359.9 |  | 調整 |
| 房間 | 頂樓檯燈 灯 | `light.yeelink_lamp2_678c_light` | light | 242.6 | 42.9 |  | 調整 |
| 房間 | 四樓樓梯燈 灯 | `light.yeelink_color5_0fb7_light` | light | 385.5 | 448.0 |  | 原圖 |
| 房間 | 頂樓崁燈 | `light.ding_lou_kan_deng` | light | 411.4 | 321.5 | 5f_房間_lights_3 | 調整 |
| 房間 | 頂樓燈組1 | `light.ding_lou_deng_zu_1` | light | 412.5 | 172.5 | 5f_房間_lights_3 | 調整 |
| 房間 | 頂樓燈組2 | `light.ding_lou_deng_zu_2` | light | 413.2 | 232.1 | 5f_房間_lights_3 | 調整 |
| 房間 | 床頭燈 灯 | `light.yeelink_bslamp2_4329_light` | light | 577.0 | 36.0 | 5f_房間_lights_5 | 原圖 |
| 房間 | 頂樓HomePod | `media_player.ding_lou_homepod` | media_player | 504.0 | 340.5 |  | 原圖 |
| 房間 | 書房感應開關 Motion Left | `binary_sensor.shu_fang_gan_ying_kai_guan_motion_left` | motion | 599.66 | 302.75 |  | 原圖 |
| 房間 | 五樓印表機 | `switch.cha_zuo_1` | plug | 308.5 | 446.4 |  | 原圖 |
| 房間 | switch.asusworkstationcha_zuo1 | `switch.asusworkstationcha_zuo1` | plug | 398.5 | 62.5 |  | 原圖 ⚠HA無此實體 |
| 房間 | AsusWorkstation插座 | `switch.asusworkstationcha_zuo` | plug | 429.6 | 29.5 |  | 原圖 |
| 房間 | TP-LINK_Power Strip_028A 頂樓Homepod插座 | `switch.ding_lou_homepodcha_zuo` | plug | 513.0 | 359.4 |  | 原圖 |
| 房間 | TP-LINK_Power Strip_028A 小燕網關插座 | `switch.xiao_yan_wang_guan_cha_zuo` | plug | 529.0 | 359.4 |  | 原圖 |
| 房間 | RICOH SP C261SFNw | `sensor.ricoh_sp_c261sfnw` | printer | 308.0 | 420.0 |  | 原圖 |
| 房間 | 壁燈 | `switch.bi_deng` | switch | 588.1 | 132.2 | 5f_房間_lights_5 | 調整 |
| 房間 | 頂樓溫度(Homepod) | `sensor.5f_homepodmini_temperature` | temp | 389.4 | 358.9 |  | 調整 |
| 房間 | 頂樓體感溫度 | `sensor.ding_lou_you_xiao_ti_gan_wen_du_homekitqiao_jie` | temp | 459.3 | 359.4 |  | 調整 |
| 房間 | 書房感應開關 溫度 | `sensor.shu_fang_gan_ying_kai_guan_temperature` | temp | 606.5 | 312.0 |  | 原圖 |
| 書房 | 五樓攝影機 High resolution channel | `camera.wu_lou_she_ying_ji_high` | camera | 696.64 | 466.07 |  | 原圖 |
| 書房 | 頂樓樓梯燈 灯 | `light.yeelink_color5_13b8_light` | light | 677.5 | 446.4 |  | 原圖 |
| 書房 | 書房感應開關 Motion Right | `binary_sensor.shu_fang_gan_ying_kai_guan_motion_right` | motion | 616.89 | 303.49 |  | 原圖 |
| 書房 | 頂樓攝影機 Motion | `binary_sensor.ding_lou_ding_lou_she_ying_ji_motion` | motion | 676.0 | 482.0 |  | 原圖 |
| 書房 | 五樓攝影機 動作 | `binary_sensor.wu_lou_she_ying_ji_motion` | motion | 692.5 | 480.4 |  | 原圖 |
| 書房 | 五樓攝影機 偵測到人員 | `binary_sensor.wu_lou_she_ying_ji_person_detected` | person | 692.5 | 494.2 |  | 原圖 |
| 書房 | 捕蚊燈 | `switch.sheng_dan_deng_cha_zuo` | plug | 634.0 | 283.2 |  | 原圖 |
| 書房 | 書房燈 | `switch.shu_fang_deng` | switch | 709.3 | 144.2 |  | 調整 |

