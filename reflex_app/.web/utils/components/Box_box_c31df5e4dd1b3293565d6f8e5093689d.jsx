
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_c31df5e4dd1b3293565d6f8e5093689d = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_05a0c66f49347cea4352cd21eb7172fc = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.apply_payday", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["flex"] : "2", ["padding"] : "10px", ["borderRadius"] : "8px", ["background"] : (reflex___state____state__cura___state____app_state.payday_saving_rx_state_ ? "#252535" : "#34d399"), ["color"] : "#fff", ["fontSize"] : "12px", ["textAlign"] : "center", ["cursor"] : "pointer", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["letterSpacing"] : "0.06em", ["textTransform"] : "uppercase", ["fontWeight"] : "700", ["&:hover"] : ({ ["opacity"] : "0.9" }) }),onClick:on_click_05a0c66f49347cea4352cd21eb7172fc},children)
    )
});
