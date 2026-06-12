
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_00a7c388b06739da6e215d4a216625bd = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_7ce6d2f9ccbcd638656a02ff6a0a6dbe = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_pop_apply_from", ({ ["mkey"] : "" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["&"] : ((reflex___state____state__cura___state____app_state.wi_pop_apply_from_rx_state_?.valueOf?.() === ""?.valueOf?.()) ? ({ ["padding"] : "5px 10px", ["border_radius"] : "6px", ["cursor"] : "pointer", ["font_size"] : "11px", ["font_family"] : "'JetBrains Mono', monospace", ["background"] : "#BF5AF2", ["color"] : "#fff", ["border"] : "1px solid #BF5AF2" }) : ({ ["padding"] : "5px 10px", ["border_radius"] : "6px", ["cursor"] : "pointer", ["font_size"] : "11px", ["font_family"] : "'JetBrains Mono', monospace", ["background"] : "rgba(255,255,255,0.08)", ["color"] : "#606088", ["border"] : "1px solid rgba(255,255,255,0.08)", ["_hover"] : ({ ["color"] : "#9090B8", ["border_color"] : "rgba(255,255,255,0.14)" }) })) }),onClick:on_click_7ce6d2f9ccbcd638656a02ff6a0a6dbe,role:"button",tabIndex:0},children)
    )
});
