
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_e5d827435ca1b7852ebd2eb1c387c87c = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_e9dc7af97fc39900d8081b3c8167b283 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_ledger_acct_filter", ({ ["value"] : "" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["&"] : ((reflex___state____state__cura___state____app_state.ledger_acct_filter_rx_state_?.valueOf?.() === ""?.valueOf?.()) ? ({ ["padding"] : "5px 12px", ["border_radius"] : "20px", ["font_size"] : "12px", ["font_family"] : "'Share Tech Mono', monospace", ["cursor"] : "pointer", ["color"] : "#818cf8", ["background"] : "#818cf818", ["border"] : "1px solid #818cf844", ["flex_shrink"] : "0" }) : ({ ["padding"] : "5px 12px", ["border_radius"] : "20px", ["font_size"] : "12px", ["font_family"] : "'Share Tech Mono', monospace", ["cursor"] : "pointer", ["color"] : "#6868a2", ["background"] : "#1c1c25", ["border"] : "1px solid #252535", ["flex_shrink"] : "0", ["_hover"] : ({ ["color"] : "#8282a2", ["border_color"] : "#3c3c56" }) })) }),onClick:on_click_e9dc7af97fc39900d8081b3c8167b283},children)
    )
});
