
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Dialog as RadixThemesDialog} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Dialogroot_dialog__root_ea935084f250065af5ee3a4e289344ce = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_open_change_5911a6d0c80c845cecf8a351b8d4d258 = useCallback(((_ev_0) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_payday_open", ({ ["value"] : _ev_0 }), ({  })))], [_ev_0], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesDialog.Root,{onOpenChange:on_open_change_5911a6d0c80c845cecf8a351b8d4d258,open:reflex___state____state__cura___state____app_state.payday_open_rx_state_},children)
    )
});
