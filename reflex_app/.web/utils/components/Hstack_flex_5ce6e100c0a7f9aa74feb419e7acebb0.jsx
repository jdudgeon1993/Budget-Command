
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Flex as RadixThemesFlex} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Hstack_flex_5ce6e100c0a7f9aa74feb419e7acebb0 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_a59b933c657d418ebebdcf6192492dd0 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.toggle_wi_panel", ({ ["key"] : "periods" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesFlex,{align:"start","aria-expanded":(reflex___state____state__cura___state____app_state.wi_periods_open_rx_state_ ? "true" : "false"),className:"rx-Stack",css:({ ["height"] : "44px", ["minHeight"] : "44px", ["alignItems"] : "center", ["padding"] : "0 14px", ["cursor"] : "pointer", ["background"] : "rgba(255,255,255,0.05)", ["borderBottom"] : (reflex___state____state__cura___state____app_state.wi_periods_open_rx_state_ ? "1px solid rgba(255,255,255,0.08)" : "none"), ["gap"] : "10px", ["userSelect"] : "none", ["&:hover"] : ({ ["background"] : "rgba(255,255,255,0.08)" }), ["&:focus-visible"] : ({ ["outline"] : "2px solid #BF5AF2", ["outlineOffset"] : "-2px" }), ["width"] : "100%" }),direction:"row",onClick:on_click_a59b933c657d418ebebdcf6192492dd0,role:"button",gap:"3",tabIndex:0},children)
    )
});
