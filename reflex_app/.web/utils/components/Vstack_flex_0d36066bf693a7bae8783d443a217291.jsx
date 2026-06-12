
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Flex as RadixThemesFlex} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Vstack_flex_0d36066bf693a7bae8783d443a217291 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_329a8a40aee345c72bfa3eac63546576 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_panel", ({ ["name"] : "ledger" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesFlex,{align:"start","aria-current":((reflex___state____state__cura___state____app_state.active_panel_rx_state_?.valueOf?.() === "ledger"?.valueOf?.()) ? "page" : "false"),"aria-label":"Ledger",className:"rx-Stack",css:({ ["&"] : ((reflex___state____state__cura___state____app_state.active_panel_rx_state_?.valueOf?.() === "ledger"?.valueOf?.()) ? ({ ["color"] : "#818cf8", ["cursor"] : "pointer", ["align_items"] : "center", ["gap"] : "4px", ["flex"] : "1", ["justify_content"] : "center", ["min_height"] : "44px", ["padding"] : "4px 0", ["_focus_visible"] : ({ ["outline"] : "2px solid #818cf8", ["outline_offset"] : "2px" }) }) : ({ ["color"] : "#6868a2", ["cursor"] : "pointer", ["align_items"] : "center", ["gap"] : "4px", ["flex"] : "1", ["justify_content"] : "center", ["min_height"] : "44px", ["padding"] : "4px 0", ["_focus_visible"] : ({ ["outline"] : "2px solid #818cf8", ["outline_offset"] : "2px" }) })) }),direction:"column",onClick:on_click_329a8a40aee345c72bfa3eac63546576,role:"button",gap:"3",tabIndex:0},children)
    )
});
