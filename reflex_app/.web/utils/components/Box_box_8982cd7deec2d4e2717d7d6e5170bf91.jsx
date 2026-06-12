
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_8982cd7deec2d4e2717d7d6e5170bf91 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_da6efb82cf0afd67ba67c4ec3bf33498 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.distribute_rts", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["padding"] : "6px 16px", ["borderRadius"] : "20px", ["background"] : "#818cf8", ["color"] : "#fff", ["fontSize"] : "12px", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["letterSpacing"] : "0.08em", ["cursor"] : "pointer", ["fontWeight"] : "600", ["&:hover"] : ({ ["opacity"] : "0.85" }), ["&:active"] : ({ ["transform"] : "scale(0.97)" }) }),onClick:on_click_da6efb82cf0afd67ba67c4ec3bf33498},children)
    )
});
