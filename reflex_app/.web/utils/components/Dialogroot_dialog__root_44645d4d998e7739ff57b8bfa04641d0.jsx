
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Dialog as RadixThemesDialog} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Dialogroot_dialog__root_44645d4d998e7739ff57b8bfa04641d0 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_open_change_a554394f4958c1a2d76806ef186d697f = useCallback(((_ev_0) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.close_edit_paycheck", ({  }), ({  })))], [_ev_0], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesDialog.Root,{onOpenChange:on_open_change_a554394f4958c1a2d76806ef186d697f,open:reflex___state____state__cura___state____app_state.edit_pc_open_rx_state_},children)
    )
});
