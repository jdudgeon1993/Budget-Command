
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_90c7ac260853ed1b477f76cad6d4c427 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)
const on_click_f11ea682e2ee3da5417432c03c483fea = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.open_reconcile", ({ ["acct_id"] : reflex___state____state__cura___state____app_state.ledger_acct_filter_rx_state_ }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent, reflex___state____state__cura___state____app_state])



    return(
        jsx(RadixThemesBox,{css:({ ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["fontSize"] : "11px", ["letterSpacing"] : "0.08em", ["padding"] : "8px 12px", ["borderRadius"] : "8px", ["border"] : "1px solid #30D15855", ["color"] : "#30D158", ["cursor"] : "pointer", ["whiteSpace"] : "nowrap", ["flexShrink"] : "0", ["&:hover"] : ({ ["background"] : "#30D1580d" }) }),onClick:on_click_f11ea682e2ee3da5417432c03c483fea},children)
    )
});
