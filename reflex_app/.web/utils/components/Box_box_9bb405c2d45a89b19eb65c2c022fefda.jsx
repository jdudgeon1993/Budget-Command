
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_9bb405c2d45a89b19eb65c2c022fefda = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_34c21647b3fcc3206525c129f8ee09a0 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.do_copy_allocs", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["fontSize"] : "11px", ["color"] : "#606088", ["cursor"] : "pointer", ["padding"] : "5px 10px", ["borderRadius"] : "6px", ["border"] : "1px solid rgba(255,255,255,0.08)", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["&:hover"] : ({ ["color"] : "#9090B8", ["borderColor"] : "rgba(255,255,255,0.14)" }) }),onClick:on_click_34c21647b3fcc3206525c129f8ee09a0},children)
    )
});
