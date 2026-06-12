
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_d446065423c834a56e9785eee7ce622a = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)
const on_click_d385c0a83320c3c8d8b0b0805c9213a1 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.archive_account", ({ ["aid"] : reflex___state____state__cura___state____app_state.acct_settings_aid_rx_state_ }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent, reflex___state____state__cura___state____app_state])



    return(
        jsx(RadixThemesBox,{css:({ ["flex"] : "1", ["padding"] : "9px", ["borderRadius"] : "8px", ["border"] : "1px solid #FF453A44", ["color"] : "#FF453A", ["fontSize"] : "11px", ["textAlign"] : "center", ["cursor"] : "pointer", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["&:hover"] : ({ ["background"] : "#FF453A11" }) }),onClick:on_click_d385c0a83320c3c8d8b0b0805c9213a1},children)
    )
});
