
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_93f84b9d6d9fe5a636dc3daa4e3595d9 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_5fff12264fa2fa4e2b15065998e221a1 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.save_edit_tx", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["flex"] : "2", ["padding"] : "9px", ["borderRadius"] : "8px", ["background"] : (reflex___state____state__cura___state____app_state.edit_tx_saving_rx_state_ ? "#252535" : "#818cf8"), ["color"] : "#fff", ["fontSize"] : "11px", ["textAlign"] : "center", ["cursor"] : "pointer", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["letterSpacing"] : "0.08em", ["textTransform"] : "uppercase", ["fontWeight"] : "700", ["&:hover"] : ({ ["opacity"] : "0.9" }) }),onClick:on_click_5fff12264fa2fa4e2b15065998e221a1},children)
    )
});
