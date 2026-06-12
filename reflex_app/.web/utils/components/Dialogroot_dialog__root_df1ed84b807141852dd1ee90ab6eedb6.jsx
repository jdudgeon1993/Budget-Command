
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Dialog as RadixThemesDialog} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Dialogroot_dialog__root_df1ed84b807141852dd1ee90ab6eedb6 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_open_change_c7b2364ade73d6ffb7d95ff1d5468a37 = useCallback(((_ev_0) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_rule_sheet_open", ({ ["value"] : _ev_0 }), ({  })))], [_ev_0], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesDialog.Root,{onOpenChange:on_open_change_c7b2364ade73d6ffb7d95ff1d5468a37,open:reflex___state____state__cura___state____app_state.rule_sheet_open_rx_state_},children)
    )
});
