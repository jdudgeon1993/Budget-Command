
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_979fb01bc94221c3af6c6433ef4c1cba = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_da93f7a9e6f0720f0efa5eab9792c498 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.submit_transaction", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["width"] : "100%", ["padding"] : "14px", ["background"] : (reflex___state____state__cura___state____app_state.sheet_saving_rx_state_ ? "rgba(255,255,255,0.08)" : ((reflex___state____state__cura___state____app_state.sheet_type_rx_state_?.valueOf?.() === "in"?.valueOf?.()) ? "#30D158" : ((reflex___state____state__cura___state____app_state.sheet_type_rx_state_?.valueOf?.() === "out"?.valueOf?.()) ? "#FF453A" : "#BF5AF2"))), ["color"] : "#fff", ["border"] : "none", ["borderRadius"] : "10px", ["fontSize"] : "13px", ["letterSpacing"] : "0.1em", ["textTransform"] : "uppercase", ["cursor"] : "pointer", ["textAlign"] : "center", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["fontWeight"] : "700", ["boxShadow"] : ((reflex___state____state__cura___state____app_state.sheet_type_rx_state_?.valueOf?.() === "in"?.valueOf?.()) ? "0 4px 18px rgba(48,209,88,0.35)" : ((reflex___state____state__cura___state____app_state.sheet_type_rx_state_?.valueOf?.() === "out"?.valueOf?.()) ? "0 4px 18px rgba(255,69,58,0.35)" : "0 4px 18px rgba(191,90,242,0.38)")), ["&:hover"] : ({ ["opacity"] : "0.9" }), ["&:active"] : ({ ["transform"] : "scale(0.98)" }) }),onClick:on_click_da93f7a9e6f0720f0efa5eab9792c498},children)
    )
});
