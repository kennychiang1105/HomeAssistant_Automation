"""LLM and Model Context Protocol (MCP) platform for spatial_context."""
from __future__ import annotations

import logging
from typing import Any, override

import probatio

from homeassistant.components.llm import LLMTools
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.llm import (
    LLM_API_ASSIST,
    LLMContext,
    Tool,
    ToolAnnotations,
    ToolInput,
    ToolResult,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SPATIAL_PROMPT = """
## Chiang Family 智慧家庭空間拓撲與感知座標體系 (AI 4.0 Spatial Intelligence)
本家庭建立完整的 1F~5F SVG 空間圖譜與相對方位感知體系。
- 座標體系：以各樓層圖面左上角為原點 (0, 0)，X 正向為東 (+X/向右)，Y 正向為南 (+Y/向下)。
- 常用關鍵地標與相對方位實體映射（AI 控制請依此精準定位）：
  * 【1F 車庫區】
    - 車庫鐵捲門：cover.garage（西側邊緣 x:13.0, y:212.8）
    - 前座車位 (車位一)：sensor.parkinggrid1 (x:175.0, y:184.2)
    - 後座車位 (車位二)：sensor.parkinggrid2 (x:441.5, y:184.2)
    - 車庫主照明：switch.che_ku_zhu_deng（中央天花板）
    - 特斯拉充電樁：sensor.tesla_wall_connector_status (x:470.6, y:426.5)
    - 1F往2F樓梯燈：switch.lou_ti_deng（東南梯廳）
    - 車庫攝影機：camera.g6_instant_high_resolution_channel (UniFi G4 Instant，標準橫向16:9/無走廊模式，東北角朝向 141.3° 西南偏南，水平視角 102.4°，全覽鐵捲門與雙車位)
  * 【2F 公共生活區 (客廳/餐廳/廚房/廁所)】
    - 2F正門/玄關大門鎖：lock.er_lou_men_suo (x:62.4, y:127.0)
    - 客廳沙發左後方/露台造景燈：light.yeelink_color5_lu_deng (x:62.4, y:480.1)
    - 客廳沙發旁壁燈：switch.ke_ting_bi_deng (x:196.3, y:174.8)
    - 客廳電視影音：switch.ke_ting_dian_shi (x:256.4, y:358.3)
    - 客廳筒燈群：light.ke_ting_deng_zu_tong_deng (x:193.3, y:226.5)
    - 客廳吊燈：light.ke_ting_deng_zu_diao_deng (x:319.5, y:226.5)
    - 餐廳筒燈/餐吊燈：light.can_ting_deng_zu_tong_deng / light.can_ting_deng_zu_can_diao_deng
    - 廚房主燈：switch.chu_fang_deng (x:835.1, y:198.3)
    - 廚房備料走道微波雷達 (靜止人體存在)：binary_sensor.unknown_zhan_kong (x:846.6, y:12.8，朝正南 90.0° 直射走道)
    - 廚房角落紅外線 (瞬時走入偵測)：binary_sensor.kitchen_motion (x:948.8, y:239.5，朝西北西 194.9° 橫切入口)
    - 客廁主燈：switch.ce_suo_deng (x:911.4, y:446.1)
    - 客廁過道動態感應：binary_sensor.e406bf25caa1_motion (x:855.4, y:441.7，朝正東 0.0° 正對廁所門)
    - 2F往3F樓梯燈：switch.er_san_lou_lou_ti_deng
  * 【3F 主臥室區】
    - 床頭閱讀燈：light.zhu_wo_chuang_tou_deng (x:246.5, y:248.0)
    - 主臥天花板主燈：light.zhu_wo_deng_zu_zhu_deng (x:380.0, y:248.0)
    - 主臥冷氣：climate.zhu_wo_leng_qi
    - 3F樓梯/走廊燈：switch.san_lou_lou_ti_deng
  * 【4F 次臥區】
    - 前臥室 (Elay)：switch.qian_wo_shi_deng
    - 後臥室 (Jerry)：switch.hou_wo_shi_deng
    - 4F樓梯燈：switch.san_si_lou_lou_ti_deng / switch.si_lou_lou_ti_deng
  * 【5F 頂樓/書房/陽台】
    - 5F梯廳氣氛/夜燈：light.yeelink_color5_13b8_light (x:677.5, y:446.4，樓梯抵達口)
    - 頂樓休閒大廳主燈：light.ding_lou_deng_zu_zhu_deng (x:480.0, y:303.0)
    - 書房雙向感應開關（重要方位辨識）：
      • 右側感應器 (朝正東 0° 走廊/梯廳)：binary_sensor.shu_fang_gan_ying_kai_guan_motion_right（上樓進入頂樓大廳偵測）
      • 左側感應器 (朝正西 180° 房間/書桌)：binary_sensor.shu_fang_gan_ying_kai_guan_motion_left（起身或書房活動偵測）
    - 書房工作站主機：switch.shu_fang_zhu_ji (x:210.0, y:303.0)
    - 書房周邊插座：switch.shu_fang_cha_zuo
    - 書房冷氣：climate.ding_lou_kong_diao
    - 戶外陽台照明：switch.yang_tai_deng (x:120.0, y:460.0)
    - 攝影機：camera.wu_lou_she_ying_ji_high (UniFi G6 Instant，標準橫向16:9/無走廊模式，角落朝向 203.1° 西北偏西，水平視角 109.9°，覆蓋樓梯踏步踏入點與休閒區入口)
- 空間推理與控制行為規範：
  1. 方位語義轉換：當指令提及「沙發左側」、「車庫前座」、「書房右側開關」、「廚房備料走道」時，請優先映射至上述確切實體。
  2. 若遇到複雜或未列出的空間方位，請調用 spatial_context 空間工具（如 spatial_context__query_entity 或 spatial_context__get_floor_layout）查詢實體座標與相對關係。
"""

LANDMARK_ALIASES: list[dict[str, Any]] = [
    {
        "keywords": ["沙發左", "沙發後", "落地燈", "客廳角落燈", "露台造景燈"],
        "entity_id": "light.yeelink_color5_lu_deng",
        "floor": "2F",
        "room": "2F 客廳走道/後陽台側",
        "note": "客廳西南側落地燈 / 露台造景燈，位於沙發左後方 (x:62.38, y:480.07)",
    },
    {
        "keywords": ["沙發壁燈", "客廳壁燈", "沙發旁燈"],
        "entity_id": "switch.ke_ting_bi_deng",
        "floor": "2F",
        "room": "2F 客廳沙發/影音區",
        "note": "客廳沙發旁壁燈 (x:196.29, y:174.80)",
    },
    {
        "keywords": ["車位一", "車位1", "前座車位", "前車位", "車庫前"],
        "entity_id": "sensor.parkinggrid1",
        "floor": "1F",
        "room": "1F 車庫停車區",
        "note": "車位一（前座車位偵測）(x:174.97, y:184.15)",
    },
    {
        "keywords": ["車位二", "車位2", "後座車位", "後車位", "車庫後"],
        "entity_id": "sensor.parkinggrid2",
        "floor": "1F",
        "room": "1F 車庫停車區",
        "note": "車位二（後座車位偵測）(x:441.50, y:184.16)",
    },
    {
        "keywords": ["車庫鐵捲門", "鐵捲門", "車庫門"],
        "entity_id": "cover.garage",
        "floor": "1F",
        "room": "1F 車庫停車區",
        "note": "車庫電動鐵捲門 (x:13.0, y:212.78)",
    },
    {
        "keywords": ["車庫主燈", "車庫大燈", "車庫中央燈"],
        "entity_id": "switch.che_ku_zhu_deng",
        "floor": "1F",
        "room": "1F 車庫停車區",
        "note": "車庫中央主照明開關 (x:311.02, y:184.15)",
    },
    {
        "keywords": ["特斯拉充電樁", "充電樁", "tesla"],
        "entity_id": "sensor.tesla_wall_connector_status",
        "floor": "1F",
        "room": "1F 車庫後方樓梯與設備區",
        "note": "特斯拉壁掛充電樁 (x:470.62, y:426.50)",
    },
    {
        "keywords": ["車庫攝影機", "一樓攝影機", "g4 instant", "g4攝影機"],
        "entity_id": "camera.g6_instant_high_resolution_channel",
        "floor": "1F",
        "room": "1F 車庫停車區",
        "note": "車庫 UniFi G4 Instant 攝影機 (x:387.95, y:29.42, 朝向 141.3° 西南偏南, 水平視角 102.4°)",
    },
    {
        "keywords": ["玄關大門鎖", "正門鎖", "二樓門鎖", "大門鎖"],
        "entity_id": "lock.er_lou_men_suo",
        "floor": "2F",
        "room": "2F 玄關入口區",
        "note": "2F 玄關正門智慧門鎖 (x:62.38, y:126.98)",
    },
    {
        "keywords": ["廚房微動", "廚房雷達", "備料走道", "微波雷達"],
        "entity_id": "binary_sensor.unknown_zhan_kong",
        "floor": "2F",
        "room": "2F 廚房料理區",
        "note": "廚房備料走道微波雷達人體存在感測器 (x:846.60, y:12.81, 朝向正南 90.0°)",
    },
    {
        "keywords": ["廚房角落紅外線", "廚房門口動態", "廚房pir"],
        "entity_id": "binary_sensor.kitchen_motion",
        "floor": "2F",
        "room": "2F 廚房料理區",
        "note": "廚房角落 PIR 動態感測器 (x:948.82, y:239.47, 朝向西北西 194.9°)",
    },
    {
        "keywords": ["客廁門口動態", "廁所感應", "廁所過道"],
        "entity_id": "binary_sensor.e406bf25caa1_motion",
        "floor": "2F",
        "room": "2F 廁所與樓梯過道",
        "note": "客廁門口動態感測器 (x:855.39, y:441.69, 朝向正東 0.0°)",
    },
    {
        "keywords": ["書房右側", "頂樓書房右側", "書房靠走廊感應", "頂樓右側感應"],
        "entity_id": "binary_sensor.shu_fang_gan_ying_kai_guan_motion_right",
        "floor": "5F",
        "room": "5F 頂樓休閒交誼區",
        "note": "5F感應開關右側感應器（朝向正東 0.0° 梯廳走廊）(x:616.89, y:303.49)",
    },
    {
        "keywords": ["書房左側", "頂樓書房左側", "書房靠房間感應", "頂樓左側感應", "書桌感應"],
        "entity_id": "binary_sensor.shu_fang_gan_ying_kai_guan_motion_left",
        "floor": "5F",
        "room": "5F 頂樓休閒交誼區",
        "note": "5F感應開關左側感應器（朝向正西 180.0° 房間與書桌）(x:599.66, y:302.75)",
    },
    {
        "keywords": ["頂樓攝影機", "五樓攝影機", "g6 instant", "g6攝影機"],
        "entity_id": "camera.wu_lou_she_ying_ji_high",
        "floor": "5F",
        "room": "5F 樓梯口與監控角",
        "note": "5F 角落 UniFi G6 Instant 攝影機 (x:696.64, y:466.07, 朝向 203.1° 西北偏西, 水平視角 109.9°)",
    },
    {
        "keywords": ["五樓梯廳燈", "頂樓樓梯口燈", "頂樓夜燈", "梯廳氣氛燈"],
        "entity_id": "light.yeelink_color5_13b8_light",
        "floor": "5F",
        "room": "5F 樓梯口與監控角",
        "note": "5F 梯廳彩色氣氛與夜燈 (x:677.50, y:446.36)",
    },
    {
        "keywords": ["書房主機", "頂樓電腦主機", "工作站主機"],
        "entity_id": "switch.shu_fang_zhu_ji",
        "floor": "5F",
        "room": "5F 書房辦公區",
        "note": "5F 書房工作站電腦主機供電 (x:210.00, y:303.00)",
    },
    {
        "keywords": ["頂樓陽台燈", "五樓陽台燈", "露台燈"],
        "entity_id": "switch.yang_tai_deng",
        "floor": "5F",
        "room": "5F 頂樓戶外陽台",
        "note": "5F 戶外陽台照明 (x:120.00, y:460.00)",
    },
]


class SpatialQueryEntityTool(Tool):
    """Tool to query entities by spatial semantics and coordinates."""

    name = "spatial_context__query_entity"
    title = "Query Entity by Spatial Semantics"
    description = (
        "Find Home Assistant entities by natural language spatial location, relative "
        "directions, landmark names, or Chinese spatial keywords (e.g., '沙發左後方的燈', "
        "'車位一', '頂樓書房右側感應開關', '廚房備料走道微動雷達', '特斯拉充電樁'). "
        "Returns matching entity IDs, coordinates, room, current state, and spatial relationship notes."
    )
    integration = DOMAIN
    annotations = ToolAnnotations(
        read_only=True, destructive=False, idempotent=True, open_world=False
    )

    def __init__(self, hass: HomeAssistant) -> None:
        """Init the tool."""
        self.hass = hass
        self.parameters = probatio.Schema(
            {
                probatio.Required(
                    "query",
                    description="Spatial location description, relative direction, or landmark name",
                ): str,
                probatio.Optional(
                    "floor",
                    description="Optional floor filter (1F, 2F, 3F, 4F, 5F)",
                ): str,
                probatio.Optional(
                    "domain",
                    description="Optional entity domain filter (e.g., light, switch, binary_sensor, cover, sensor, camera)",
                ): str,
            }
        )

    @override
    async def async_call(
        self, hass: HomeAssistant, tool_input: ToolInput, llm_context: LLMContext
    ) -> ToolResult:
        """Execute spatial entity query."""
        data = self.parameters(tool_input.tool_args)
        query = str(data["query"]).strip().lower()
        floor_filter = data.get("floor")
        domain_filter = data.get("domain")
        if floor_filter:
            floor_filter = floor_filter.upper()
        if domain_filter:
            domain_filter = domain_filter.lower()

        matched_entities: dict[str, dict[str, Any]] = {}

        # 1. Check Landmark Aliases
        for alias in LANDMARK_ALIASES:
            ent_id = alias["entity_id"]
            alias_floor = alias.get("floor", "")
            if floor_filter and alias_floor and floor_filter != alias_floor:
                continue
            if domain_filter and not ent_id.startswith(domain_filter + "."):
                continue

            hit = any(kw.lower() in query or query in kw.lower() for kw in alias["keywords"])
            if hit:
                state_obj = hass.states.get(ent_id)
                friendly_name = state_obj.name if state_obj else ent_id
                current_state = state_obj.state if state_obj else "unknown"
                matched_entities[ent_id] = {
                    "entity_id": ent_id,
                    "name": friendly_name,
                    "floor": alias_floor,
                    "room": alias.get("room", ""),
                    "state": current_state,
                    "note": alias.get("note", ""),
                }

        # 2. Check Scene Graph
        spatial_data = hass.data.get(DOMAIN, {})
        scene_graph = spatial_data.get("scene_graph", {})
        floors = scene_graph.get("floors", {})

        for f_name, f_info in floors.items():
            if floor_filter and f_name.upper() != floor_filter:
                continue

            for ent in f_info.get("entities", []):
                ent_id = ent.get("entity_id", "")
                ent_domain = ent.get("domain", "")
                if domain_filter and ent_domain != domain_filter:
                    continue

                state_obj = hass.states.get(ent_id)
                friendly_name = state_obj.name if state_obj else ent_id
                room = ent.get("room", "")
                coords = ent.get("coordinates", {})

                # Check if query matches entity_id, room, or friendly name
                q_hit = (
                    query in ent_id.lower()
                    or query in room.lower()
                    or (friendly_name and query in friendly_name.lower())
                )
                if q_hit:
                    current_state = state_obj.state if state_obj else "unknown"
                    matched_entities[ent_id] = {
                        "entity_id": ent_id,
                        "name": friendly_name,
                        "floor": f_name,
                        "room": room,
                        "coordinates": coords,
                        "state": current_state,
                        "note": f"位於 {f_name} {room} (x:{coords.get('x')}, y:{coords.get('y')})",
                    }

        results = list(matched_entities.values())
        return ToolResult(
            data={
                "query": query,
                "count": len(results),
                "matches": results[:10],
            }
        )


class SpatialGetFloorLayoutTool(Tool):
    """Tool to retrieve full floor spatial layout and entity locations."""

    name = "spatial_context__get_floor_layout"
    title = "Get Floor Spatial Layout"
    description = (
        "Retrieve the complete SVG coordinate layout, room zones, and situated entities "
        "for a specific floor (1F, 2F, 3F, 4F, or 5F)."
    )
    integration = DOMAIN
    annotations = ToolAnnotations(
        read_only=True, destructive=False, idempotent=True, open_world=False
    )

    def __init__(self, hass: HomeAssistant) -> None:
        """Init the tool."""
        self.hass = hass
        self.parameters = probatio.Schema(
            {
                probatio.Required(
                    "floor",
                    description="Floor identifier: 1F, 2F, 3F, 4F, or 5F",
                ): probatio.In(["1F", "2F", "3F", "4F", "5F", "1f", "2f", "3f", "4f", "5f"]),
            }
        )

    @override
    async def async_call(
        self, hass: HomeAssistant, tool_input: ToolInput, llm_context: LLMContext
    ) -> ToolResult:
        """Retrieve floor layout."""
        data = self.parameters(tool_input.tool_args)
        floor_key = str(data["floor"]).upper()

        spatial_data = hass.data.get(DOMAIN, {})
        scene_graph = spatial_data.get("scene_graph", {})
        floor_info = scene_graph.get("floors", {}).get(floor_key)

        if not floor_info:
            return ToolResult(data={"error": f"Floor '{floor_key}' not found in scene graph"}, error=True)

        entities_list: list[dict[str, Any]] = []
        for ent in floor_info.get("entities", []):
            ent_id = ent.get("entity_id", "")
            state_obj = hass.states.get(ent_id)
            entities_list.append(
                {
                    "entity_id": ent_id,
                    "name": state_obj.name if state_obj else ent_id,
                    "domain": ent.get("domain", ""),
                    "room": ent.get("room", ""),
                    "coordinates": ent.get("coordinates", {}),
                    "state": state_obj.state if state_obj else "unknown",
                }
            )

        return ToolResult(
            data={
                "floor": floor_key,
                "name": floor_info.get("name", ""),
                "viewbox": floor_info.get("viewbox", []),
                "entities_count": len(entities_list),
                "entities": entities_list,
            }
        )


class SpatialGetSensorGeometryTool(Tool):
    """Tool to get camera and motion sensor angles, FOV, and geometry."""

    name = "spatial_context__get_sensor_geometry"
    title = "Get Sensor & Camera Geometry"
    description = (
        "Retrieve installation coordinates, yaw angles, field-of-view (FOV), beam coverage, "
        "and blind spots for security cameras, microwave radar, and PIR motion sensors."
    )
    integration = DOMAIN
    annotations = ToolAnnotations(
        read_only=True, destructive=False, idempotent=True, open_world=False
    )

    def __init__(self, hass: HomeAssistant) -> None:
        """Init the tool."""
        self.hass = hass
        self.parameters = probatio.Schema(
            {
                probatio.Optional(
                    "category",
                    description="Category: 'all', 'cameras', 'motion_sensors', 'vertical_circulation'",
                    default="all",
                ): probatio.In(["all", "cameras", "motion_sensors", "vertical_circulation"]),
            }
        )

    @override
    async def async_call(
        self, hass: HomeAssistant, tool_input: ToolInput, llm_context: LLMContext
    ) -> ToolResult:
        """Retrieve geometry data."""
        data = self.parameters(tool_input.tool_args)
        category = data.get("category", "all")

        cameras = [
            {
                "entity_id": "camera.g6_instant_high_resolution_channel",
                "model": "UniFi Protect G4 Instant (UVC-G4-INS)",
                "orientation": "標準橫向安裝 (無走廊模式, 16:9)",
                "floor": "1F",
                "coordinates": {"x": 387.95, "y": 29.42},
                "yaw_deg": 141.3,
                "cardinal": "西南偏南 (SW)",
                "fov_horizontal_deg": 102.4,
                "fov_vertical_deg": 54.9,
                "fov_diagonal_deg": 120.6,
                "coverage": "車庫鐵捲門內外、車位一、車位二、中央人車動線",
                "blind_spot": "攝影機正後方東北角落死角",
            },
            {
                "entity_id": "camera.wu_lou_she_ying_ji_high",
                "model": "UniFi Protect G6 Instant (UVC-G6-INS)",
                "orientation": "標準橫向安裝 (無走廊模式, 16:9)",
                "floor": "5F",
                "coordinates": {"x": 696.64, "y": 466.07},
                "yaw_deg": 203.1,
                "cardinal": "西北偏西 (WNW)",
                "fov_horizontal_deg": 109.9,
                "fov_vertical_deg": 56.7,
                "fov_diagonal_deg": 134.1,
                "coverage": "4F上5F樓梯踏步口、5F梯廳走廊、休閒大廳主走道",
                "blind_spot": "5F東南側設備牆死角",
            },
        ]

        motion_sensors = [
            {
                "entity_id": "binary_sensor.unknown_zhan_kong",
                "type": "微波雷達 (Microwave Radar)",
                "floor": "2F",
                "room": "廚房料理區",
                "coordinates": {"x": 846.60, "y": 12.81},
                "yaw_deg": 90.0,
                "cardinal": "正南 (S)",
                "coverage": "垂直照射廚房備料走道，極佳靜止微動感應",
            },
            {
                "entity_id": "binary_sensor.kitchen_motion",
                "type": "被動紅外線 (PIR)",
                "floor": "2F",
                "room": "廚房料理區",
                "coordinates": {"x": 948.82, "y": 239.47},
                "yaw_deg": 194.9,
                "cardinal": "西北西 (WNW)",
                "coverage": "橫切餐廳與廚房交界，偵測瞬時走入動作",
            },
            {
                "entity_id": "binary_sensor.e406bf25caa1_motion",
                "type": "被動紅外線 (PIR)",
                "floor": "2F",
                "room": "廁所與樓梯過道",
                "coordinates": {"x": 855.39, "y": 441.69},
                "yaw_deg": 0.0,
                "cardinal": "正東 (E)",
                "coverage": "正對客廁門扉與通道，偵測如廁與通道進出",
            },
            {
                "entity_id": "binary_sensor.shu_fang_gan_ying_kai_guan_motion_right",
                "type": "雙向感應右側 PIR",
                "floor": "5F",
                "room": "頂樓休閒交誼區",
                "coordinates": {"x": 616.89, "y": 303.49},
                "yaw_deg": 0.0,
                "cardinal": "正東 (E)",
                "coverage": "【重要】朝向5F梯廳走廊，捕捉從樓梯走入頂樓的人員",
            },
            {
                "entity_id": "binary_sensor.shu_fang_gan_ying_kai_guan_motion_left",
                "type": "雙向感應左側 PIR",
                "floor": "5F",
                "room": "頂樓休閒交誼區",
                "coordinates": {"x": 599.66, "y": 302.75},
                "yaw_deg": 180.0,
                "cardinal": "正西 (W)",
                "coverage": "【重要】朝向書房書桌與陽台門，捕捉自書房起身或陽台返回的人員",
            },
        ]

        vertical_circulation = [
            {"portal": "1F 梯廳 ➔ 2F 餐廳", "switch": "switch.lou_ti_deng"},
            {"portal": "2F 餐廳 ➔ 3F 主臥梯廳", "switch": "switch.er_san_lou_lou_ti_deng"},
            {"portal": "3F 梯廳 ➔ 4F 次臥梯廳", "switch": "switch.san_si_lou_lou_ti_deng"},
            {"portal": "4F 梯廳 ➔ 5F 頂樓梯廳", "switch": "switch.si_lou_lou_ti_deng"},
        ]

        result_payload: dict[str, Any] = {}
        if category in ("all", "cameras"):
            result_payload["cameras"] = cameras
        if category in ("all", "motion_sensors"):
            result_payload["motion_sensors"] = motion_sensors
        if category in ("all", "vertical_circulation"):
            result_payload["vertical_circulation"] = vertical_circulation

        return ToolResult(data=result_payload)


@callback
def async_get_tools(
    hass: HomeAssistant, llm_context: LLMContext, api_id: str
) -> LLMTools | None:
    """Return spatial tools and prompt for LLM / MCP Server."""
    if api_id != LLM_API_ASSIST:
        return None

    tools: list[Tool] = [
        SpatialQueryEntityTool(hass),
        SpatialGetFloorLayoutTool(hass),
        SpatialGetSensorGeometryTool(hass),
    ]
    return LLMTools(tools=tools, prompt=SPATIAL_PROMPT)
