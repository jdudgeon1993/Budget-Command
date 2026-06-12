
import {Fragment,memo,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {Box as RadixThemesBox,Flex as RadixThemesFlex} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Foreach_comp_b23b72a818b181353ac11e5735d1d3ed = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)
const [addEvents, connectErrors] = useContext(EventLoopContext);



    return(
        Array.prototype.map.call(reflex___state____state__cura___state____app_state.wi_scenarios_rx_state_ ?? [],((sc_rx_state_,index_778389a3bc93905e10c81043773cd4b9)=>(jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["gap"] : "4px", ["alignItems"] : "center", ["width"] : "100%" }),direction:"row",key:index_778389a3bc93905e10c81043773cd4b9,gap:"3"},jsx(RadixThemesBox,{css:({ ["&"] : ((reflex___state____state__cura___state____app_state.wi_active_scenario_id_rx_state_?.valueOf?.() === sc_rx_state_?.["id"]?.valueOf?.()) ? ({ ["flex"] : "1", ["padding"] : "5px 8px", ["border_radius"] : "6px", ["cursor"] : "pointer", ["font_size"] : "11px", ["font_family"] : "'JetBrains Mono', monospace", ["background"] : "#BF5AF218", ["color"] : "#BF5AF2", ["border"] : "1px solid #BF5AF244", ["overflow"] : "hidden", ["text_overflow"] : "ellipsis", ["white_space"] : "nowrap" }) : ({ ["flex"] : "1", ["padding"] : "5px 8px", ["border_radius"] : "6px", ["cursor"] : "pointer", ["font_size"] : "11px", ["font_family"] : "'JetBrains Mono', monospace", ["background"] : "rgba(255,255,255,0.08)", ["color"] : "#9090B8", ["border"] : "1px solid rgba(255,255,255,0.08)", ["overflow"] : "hidden", ["text_overflow"] : "ellipsis", ["white_space"] : "nowrap", ["_hover"] : ({ ["border_color"] : "rgba(255,255,255,0.14)" }) })) }),onClick:((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.load_wi_scenario", ({ ["sid"] : sc_rx_state_?.["id"] }), ({  })))], [_e], ({  }))))},sc_rx_state_?.["name"]),jsx(RadixThemesBox,{css:({ ["fontSize"] : "14px", ["color"] : "#606088", ["cursor"] : "pointer", ["padding"] : "2px 5px", ["borderRadius"] : "4px", ["flexShrink"] : "0", ["&:hover"] : ({ ["color"] : "#FF453A" }) }),onClick:((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.delete_wi_scenario", ({ ["sid"] : sc_rx_state_?.["id"] }), ({  })))], [_e], ({  }))))},"\u00d7")))))
    )
});
