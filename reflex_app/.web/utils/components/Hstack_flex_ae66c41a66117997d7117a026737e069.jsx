
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Flex as RadixThemesFlex} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Hstack_flex_ae66c41a66117997d7117a026737e069 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_37254c95d5068cc62fc63ce640687a86 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.toggle_wi_panel", ({ ["key"] : "grid" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesFlex,{align:"start","aria-expanded":(reflex___state____state__cura___state____app_state.wi_grid_open_rx_state_ ? "true" : "false"),className:"rx-Stack",css:({ ["height"] : "44px", ["minHeight"] : "44px", ["alignItems"] : "center", ["padding"] : "0 14px", ["cursor"] : "pointer", ["background"] : "rgba(255,255,255,0.05)", ["borderBottom"] : (reflex___state____state__cura___state____app_state.wi_grid_open_rx_state_ ? "1px solid rgba(255,255,255,0.08)" : "none"), ["gap"] : "10px", ["userSelect"] : "none", ["&:hover"] : ({ ["background"] : "rgba(255,255,255,0.08)" }), ["&:focus-visible"] : ({ ["outline"] : "2px solid #BF5AF2", ["outlineOffset"] : "-2px" }), ["width"] : "100%" }),direction:"row",onClick:on_click_37254c95d5068cc62fc63ce640687a86,role:"button",gap:"3",tabIndex:0},children)
    )
});
