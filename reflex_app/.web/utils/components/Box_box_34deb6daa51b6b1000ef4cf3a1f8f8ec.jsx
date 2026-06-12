
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_34deb6daa51b6b1000ef4cf3a1f8f8ec = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_f56dc8b233aa515854cfd3c91d6b79fe = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.save_add_account", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["flex"] : "2", ["padding"] : "9px", ["borderRadius"] : "8px", ["background"] : (reflex___state____state__cura___state____app_state.add_acct_saving_rx_state_ ? "#252535" : "#818cf8"), ["color"] : "#fff", ["fontSize"] : "11px", ["textAlign"] : "center", ["cursor"] : "pointer", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["letterSpacing"] : "0.06em", ["textTransform"] : "uppercase", ["&:hover"] : ({ ["opacity"] : "0.9" }) }),onClick:on_click_f56dc8b233aa515854cfd3c91d6b79fe},children)
    )
});
