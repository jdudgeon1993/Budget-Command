
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_8f23e1c14097e9b05d076986e7da1fa9 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_e0f2e090aec99de6f4c8d7ce3f761635 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.add_paycheck_submit", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["padding"] : "8px 14px", ["borderRadius"] : "8px", ["background"] : (reflex___state____state__cura___state____app_state.setup_pc_saving_rx_state_ ? "rgba(255,255,255,0.08)" : "#BF5AF2"), ["color"] : "#fff", ["fontSize"] : "11px", ["cursor"] : "pointer", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["whiteSpace"] : "nowrap", ["flexShrink"] : "0", ["&:hover"] : ({ ["opacity"] : "0.9" }) }),onClick:on_click_e0f2e090aec99de6f4c8d7ce3f761635},children)
    )
});
