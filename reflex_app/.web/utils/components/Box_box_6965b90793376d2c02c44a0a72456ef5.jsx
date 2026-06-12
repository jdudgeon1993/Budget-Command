
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_6965b90793376d2c02c44a0a72456ef5 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_5fff12264fa2fa4e2b15065998e221a1 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.save_edit_tx", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["flex"] : "2", ["padding"] : "10px", ["borderRadius"] : "8px", ["background"] : (reflex___state____state__cura___state____app_state.edit_tx_saving_rx_state_ ? "rgba(255,255,255,0.08)" : "#BF5AF2"), ["color"] : "#fff", ["fontSize"] : "12px", ["textAlign"] : "center", ["cursor"] : "pointer", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["letterSpacing"] : "0.08em", ["textTransform"] : "uppercase", ["fontWeight"] : "700", ["&:hover"] : ({ ["opacity"] : "0.9" }) }),onClick:on_click_5fff12264fa2fa4e2b15065998e221a1},children)
    )
});
