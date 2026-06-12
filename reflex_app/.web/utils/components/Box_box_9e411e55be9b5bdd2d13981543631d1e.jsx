
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_9e411e55be9b5bdd2d13981543631d1e = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_dc4ca4fd007a63ead8351890c0e372cb = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.apply_pop_rule", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["width"] : "100%", ["padding"] : "12px", ["borderRadius"] : "8px", ["cursor"] : "pointer", ["fontSize"] : "13px", ["fontWeight"] : "600", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["textAlign"] : "center", ["background"] : "#BF5AF2", ["color"] : "#fff", ["border"] : "none", ["boxShadow"] : "0 4px 16px rgba(191,90,242,0.30)", ["&:hover"] : ({ ["opacity"] : "0.9" }), ["&:active"] : ({ ["transform"] : "scale(0.98)" }) }),onClick:on_click_dc4ca4fd007a63ead8351890c0e372cb,role:"button",tabIndex:0},children)
    )
});
