
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Dialog as RadixThemesDialog} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Dialogroot_dialog__root_6a98b5ae86c0e5474fd713f50642dfad = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_open_change_45c9c78e3fa5056d8bc446a4b7ba6aea = useCallback(((_ev_0) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_add_acct_open", ({ ["value"] : _ev_0 }), ({  })))], [_ev_0], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesDialog.Root,{onOpenChange:on_open_change_45c9c78e3fa5056d8bc446a4b7ba6aea,open:reflex___state____state__cura___state____app_state.add_acct_open_rx_state_},children)
    )
});
