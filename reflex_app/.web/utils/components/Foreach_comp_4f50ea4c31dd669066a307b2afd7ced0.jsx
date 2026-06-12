
import {Fragment,memo,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Foreach_comp_4f50ea4c31dd669066a307b2afd7ced0 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)
const [addEvents, connectErrors] = useContext(EventLoopContext);



    return(
        Array.prototype.map.call(reflex___state____state__cura___state____app_state.wi_grid_months_rx_state_ ?? [],((m_rx_state_,index_bde7dbc389ae88759525f649ad91d331)=>(jsx(RadixThemesBox,{css:({ ["&"] : ((reflex___state____state__cura___state____app_state.wi_pop_apply_from_rx_state_?.valueOf?.() === m_rx_state_?.["mkey"]?.valueOf?.()) ? ({ ["padding"] : "5px 10px", ["border_radius"] : "6px", ["cursor"] : "pointer", ["font_size"] : "11px", ["font_family"] : "'JetBrains Mono', monospace", ["background"] : "#BF5AF2", ["color"] : "#fff", ["border"] : "1px solid #BF5AF2" }) : ({ ["padding"] : "5px 10px", ["border_radius"] : "6px", ["cursor"] : "pointer", ["font_size"] : "11px", ["font_family"] : "'JetBrains Mono', monospace", ["background"] : "rgba(255,255,255,0.08)", ["color"] : "#606088", ["border"] : "1px solid rgba(255,255,255,0.08)", ["_hover"] : ({ ["color"] : "#9090B8", ["border_color"] : "rgba(255,255,255,0.14)" }) })) }),key:index_bde7dbc389ae88759525f649ad91d331,onClick:((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_pop_apply_from", ({ ["mkey"] : m_rx_state_?.["mkey"] }), ({  })))], [_e], ({  })))),role:"button",tabIndex:0},m_rx_state_?.["label"]))))
    )
});
