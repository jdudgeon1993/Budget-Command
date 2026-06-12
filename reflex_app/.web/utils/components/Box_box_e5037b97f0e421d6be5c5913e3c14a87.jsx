
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_e5037b97f0e421d6be5c5913e3c14a87 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_27c2bbad3ed55db4c17cdb73bc0030a9 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.add_bucket_submit", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["padding"] : "9px 16px", ["borderRadius"] : "8px", ["background"] : (reflex___state____state__cura___state____app_state.add_bkt_saving_rx_state_ ? "#252535" : "#818cf8"), ["color"] : "#fff", ["fontSize"] : "13px", ["cursor"] : "pointer", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["letterSpacing"] : "0.06em", ["whiteSpace"] : "nowrap", ["flexShrink"] : "0", ["&:hover"] : ({ ["opacity"] : "0.9" }) }),onClick:on_click_27c2bbad3ed55db4c17cdb73bc0030a9},children)
    )
});
