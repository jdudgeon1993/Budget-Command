
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_90bcc47f5e4fae34272a6a95233e08fc = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)
const on_click_5213d09dba73909ec14c795434c32ccd = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.archive_bucket_confirm", ({ ["bid"] : reflex___state____state__cura___state____app_state.bsettings_bid_rx_state_ }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent, reflex___state____state__cura___state____app_state])



    return(
        jsx(RadixThemesBox,{css:({ ["flex"] : "1", ["padding"] : "10px", ["borderRadius"] : "8px", ["border"] : "1px solid #FF453A44", ["color"] : "#FF453A", ["fontSize"] : "12px", ["textAlign"] : "center", ["cursor"] : "pointer", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["letterSpacing"] : "0.06em", ["&:hover"] : ({ ["background"] : "#FF453A11" }) }),onClick:on_click_5213d09dba73909ec14c795434c32ccd},children)
    )
});
