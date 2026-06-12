
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_a69d60b096f9ffdfa38c0269d917ff8a = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_798748479b8785dca479cb27e1e55f03 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_pop_enabled", ({ ["v"] : false }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["&"] : (!(reflex___state____state__cura___state____app_state.wi_pop_enabled_rx_state_) ? ({ ["padding"] : "6px 14px", ["border_radius"] : "6px", ["cursor"] : "pointer", ["font_size"] : "12px", ["font_family"] : "'JetBrains Mono', monospace", ["background"] : "#FF453A18", ["color"] : "#FF453A", ["border"] : "1px solid #FF453A44" }) : ({ ["padding"] : "6px 14px", ["border_radius"] : "6px", ["cursor"] : "pointer", ["font_size"] : "12px", ["font_family"] : "'JetBrains Mono', monospace", ["background"] : "rgba(255,255,255,0.08)", ["color"] : "#606088", ["border"] : "1px solid rgba(255,255,255,0.08)", ["_hover"] : ({ ["border_color"] : "rgba(255,255,255,0.14)" }) })) }),onClick:on_click_798748479b8785dca479cb27e1e55f03,role:"button",tabIndex:0},children)
    )
});
