
import {Fragment,memo,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Foreach_comp_3deb5182d334b81258e5ec6eebe61b40 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)
const [addEvents, connectErrors] = useContext(EventLoopContext);



    return(
        Array.prototype.map.call(reflex___state____state__cura___state____app_state.wi_scenarios_rx_state_ ?? [],((sc_rx_state_,index_7d0febf887cc77852967ab5b5c1d7375)=>(jsx(RadixThemesBox,{css:({ ["&"] : ((reflex___state____state__cura___state____app_state.fc_active_scenario_id_rx_state_?.valueOf?.() === sc_rx_state_?.["id"]?.valueOf?.()) ? ({ ["padding"] : "3px 10px", ["border_radius"] : "16px", ["cursor"] : "pointer", ["font_size"] : "11px", ["font_family"] : "'Share Tech Mono', monospace", ["background"] : "#fbbf2422", ["color"] : "#fbbf24", ["border"] : "1px solid #fbbf2455" }) : ({ ["padding"] : "3px 10px", ["border_radius"] : "16px", ["cursor"] : "pointer", ["font_size"] : "11px", ["font_family"] : "'Share Tech Mono', monospace", ["background"] : "#1c1c25", ["color"] : "#6868a2", ["border"] : "1px solid #252535", ["_hover"] : ({ ["color"] : "#8282a2", ["border_color"] : "#3c3c56" }) })) }),key:index_7d0febf887cc77852967ab5b5c1d7375,onClick:((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.apply_fc_scenario", ({ ["sid"] : sc_rx_state_?.["id"] }), ({  })))], [_e], ({  }))))},sc_rx_state_?.["name"]))))
    )
});
