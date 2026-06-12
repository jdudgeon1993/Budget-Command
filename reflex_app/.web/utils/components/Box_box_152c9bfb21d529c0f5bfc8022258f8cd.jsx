
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_152c9bfb21d529c0f5bfc8022258f8cd = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_85122ae0498bd9e6b60d54158217bfb7 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.save_edit_paycheck", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["padding"] : "8px 16px", ["borderRadius"] : "8px", ["background"] : (reflex___state____state__cura___state____app_state.edit_pc_saving_rx_state_ ? "rgba(255,255,255,0.08)" : "#BF5AF2"), ["color"] : "#fff", ["fontSize"] : "12px", ["cursor"] : "pointer", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["&:hover"] : ({ ["opacity"] : "0.9" }) }),onClick:on_click_85122ae0498bd9e6b60d54158217bfb7},children)
    )
});
