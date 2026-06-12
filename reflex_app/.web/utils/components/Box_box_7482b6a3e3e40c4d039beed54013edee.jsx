
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_7482b6a3e3e40c4d039beed54013edee = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_e9dc7af97fc39900d8081b3c8167b283 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_ledger_acct_filter", ({ ["value"] : "" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["&"] : ((reflex___state____state__cura___state____app_state.ledger_acct_filter_rx_state_?.valueOf?.() === ""?.valueOf?.()) ? ({ ["padding"] : "5px 12px", ["border_radius"] : "20px", ["font_size"] : "12px", ["font_family"] : "'JetBrains Mono', monospace", ["cursor"] : "pointer", ["color"] : "#BF5AF2", ["background"] : "#BF5AF218", ["border"] : "1px solid #BF5AF244", ["flex_shrink"] : "0" }) : ({ ["padding"] : "5px 12px", ["border_radius"] : "20px", ["font_size"] : "12px", ["font_family"] : "'JetBrains Mono', monospace", ["cursor"] : "pointer", ["color"] : "#606088", ["background"] : "rgba(255,255,255,0.08)", ["border"] : "1px solid rgba(255,255,255,0.08)", ["flex_shrink"] : "0", ["_hover"] : ({ ["color"] : "#9090B8", ["border_color"] : "rgba(255,255,255,0.14)" }) })) }),onClick:on_click_e9dc7af97fc39900d8081b3c8167b283},children)
    )
});
