
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_de0e9b7fe4f59f0a0c098c2a41d367cf = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_2ad91ce50fab60a911546aaa36ea057e = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.save_debt_payment", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["flex"] : "2", ["padding"] : "9px", ["borderRadius"] : "8px", ["background"] : (reflex___state____state__cura___state____app_state.debt_pay_saving_rx_state_ ? "rgba(255,255,255,0.08)" : "#FF9F0A"), ["color"] : "#fff", ["fontSize"] : "11px", ["textAlign"] : "center", ["cursor"] : "pointer", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["letterSpacing"] : "0.06em", ["textTransform"] : "uppercase", ["&:hover"] : ({ ["opacity"] : "0.9" }) }),onClick:on_click_2ad91ce50fab60a911546aaa36ea057e},children)
    )
});
