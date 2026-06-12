
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_22c0e05bc9213a91659709d72b75ea09 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_d464fd0108fb5ee81f55fdde820c8d23 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_pop_enabled", ({ ["v"] : true }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["&"] : (reflex___state____state__cura___state____app_state.wi_pop_enabled_rx_state_ ? ({ ["padding"] : "6px 14px", ["border_radius"] : "6px", ["cursor"] : "pointer", ["font_size"] : "12px", ["font_family"] : "'JetBrains Mono', monospace", ["background"] : "#30D15822", ["color"] : "#30D158", ["border"] : "1px solid #30D15855" }) : ({ ["padding"] : "6px 14px", ["border_radius"] : "6px", ["cursor"] : "pointer", ["font_size"] : "12px", ["font_family"] : "'JetBrains Mono', monospace", ["background"] : "rgba(255,255,255,0.08)", ["color"] : "#606088", ["border"] : "1px solid rgba(255,255,255,0.08)", ["_hover"] : ({ ["border_color"] : "rgba(255,255,255,0.14)" }) })) }),onClick:on_click_d464fd0108fb5ee81f55fdde820c8d23,role:"button",tabIndex:0},children)
    )
});
