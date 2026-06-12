
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_9c01ae9824d4b4febd4a6d16dbb702ef = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)
const on_click_355d2aba5c8fb87def22efef8ea8da03 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_edit_tx_reconciled", ({ ["value"] : !(reflex___state____state__cura___state____app_state.edit_tx_reconciled_rx_state_) }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent, reflex___state____state__cura___state____app_state])



    return(
        jsx(RadixThemesBox,{onClick:on_click_355d2aba5c8fb87def22efef8ea8da03},children)
    )
});
