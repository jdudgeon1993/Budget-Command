
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Dialog as RadixThemesDialog} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Dialogroot_dialog__root_a907b522e082c77535437d8dc81fa89a = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_open_change_b6b843b71b035fae23c0e466d4ce0469 = useCallback(((_ev_0) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_edit_tx_open", ({ ["v"] : _ev_0 }), ({  })))], [_ev_0], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesDialog.Root,{onOpenChange:on_open_change_b6b843b71b035fae23c0e466d4ce0469,open:reflex___state____state__cura___state____app_state.edit_tx_open_rx_state_},children)
    )
});
