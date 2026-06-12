
import {Fragment,memo,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {Box as RadixThemesBox,Flex as RadixThemesFlex} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Foreach_comp_adc9ae736b96a30ffa5d707a668ed393 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)
const [addEvents, connectErrors] = useContext(EventLoopContext);



    return(
        Array.prototype.map.call(reflex___state____state__cura___state____app_state.wi_scenarios_rx_state_ ?? [],((sc_rx_state_,index_5cbc7a124842ef00de31035db06d4155)=>(jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["gap"] : "2px", ["alignItems"] : "center" }),direction:"row",key:index_5cbc7a124842ef00de31035db06d4155,gap:"3"},jsx(RadixThemesBox,{css:({ ["&"] : ((reflex___state____state__cura___state____app_state.wi_active_scenario_id_rx_state_?.valueOf?.() === sc_rx_state_?.["id"]?.valueOf?.()) ? ({ ["padding"] : "4px 10px", ["border_radius"] : "16px", ["cursor"] : "pointer", ["font_size"] : "11px", ["font_family"] : "'Share Tech Mono', monospace", ["background"] : "#818cf818", ["color"] : "#818cf8", ["border"] : "1px solid #818cf844" }) : ({ ["padding"] : "4px 10px", ["border_radius"] : "16px", ["cursor"] : "pointer", ["font_size"] : "11px", ["font_family"] : "'Share Tech Mono', monospace", ["background"] : "#1c1c25", ["color"] : "#8282a2", ["border"] : "1px solid #252535", ["_hover"] : ({ ["border_color"] : "#3c3c56" }) })) }),onClick:((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.load_wi_scenario", ({ ["sid"] : sc_rx_state_?.["id"] }), ({  })))], [_e], ({  }))))},sc_rx_state_?.["name"]),jsx(RadixThemesBox,{css:({ ["fontSize"] : "12px", ["color"] : "#6868a2", ["cursor"] : "pointer", ["padding"] : "2px 4px", ["&:hover"] : ({ ["color"] : "#f87171" }) }),onClick:((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.delete_wi_scenario", ({ ["sid"] : sc_rx_state_?.["id"] }), ({  })))], [_e], ({  }))))},"\u00d7")))))
    )
});
