
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_e6ef75f52d9b595eff12478ba9ae377b = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)
const on_click_355d2aba5c8fb87def22efef8ea8da03 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_edit_tx_reconciled", ({ ["value"] : !(reflex___state____state__cura___state____app_state.edit_tx_reconciled_rx_state_) }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent, reflex___state____state__cura___state____app_state])



    return(
        jsx(RadixThemesBox,{"aria-label":"Toggle reconciled status","aria-pressed":(reflex___state____state__cura___state____app_state.edit_tx_reconciled_rx_state_ ? "true" : "false"),css:({ ["&:focus-visible"] : ({ ["outline"] : "2px solid #818cf8", ["outlineOffset"] : "2px", ["borderRadius"] : "6px" }) }),onClick:on_click_355d2aba5c8fb87def22efef8ea8da03,role:"button",tabIndex:0},children)
    )
});
