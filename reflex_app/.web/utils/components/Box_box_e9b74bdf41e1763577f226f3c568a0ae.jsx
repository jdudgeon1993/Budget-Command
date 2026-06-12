
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_e9b74bdf41e1763577f226f3c568a0ae = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_da93f7a9e6f0720f0efa5eab9792c498 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.submit_transaction", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["width"] : "100%", ["padding"] : "13px", ["background"] : (reflex___state____state__cura___state____app_state.sheet_saving_rx_state_ ? "#252535" : ((reflex___state____state__cura___state____app_state.sheet_type_rx_state_?.valueOf?.() === "in"?.valueOf?.()) ? "#34d399" : ((reflex___state____state__cura___state____app_state.sheet_type_rx_state_?.valueOf?.() === "out"?.valueOf?.()) ? "#f87171" : "#818cf8"))), ["color"] : "#fff", ["border"] : "none", ["borderRadius"] : "8px", ["fontSize"] : "13px", ["letterSpacing"] : "0.1em", ["textTransform"] : "uppercase", ["cursor"] : "pointer", ["textAlign"] : "center", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["fontWeight"] : "700", ["&:hover"] : ({ ["opacity"] : "0.9" }), ["&:active"] : ({ ["transform"] : "scale(0.99)" }) }),onClick:on_click_da93f7a9e6f0720f0efa5eab9792c498},children)
    )
});
