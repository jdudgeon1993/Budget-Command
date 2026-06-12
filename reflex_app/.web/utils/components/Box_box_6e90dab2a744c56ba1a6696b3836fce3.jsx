
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_6e90dab2a744c56ba1a6696b3836fce3 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_3afd465f89ffb4133e30b4f20295ae5a = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_panel", ({ ["name"] : "setup" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["marginTop"] : "12px", ["padding"] : "8px 20px", ["borderRadius"] : "8px", ["cursor"] : "pointer", ["fontSize"] : "13px", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["background"] : "#818cf818", ["color"] : "#818cf8", ["border"] : "1px solid #818cf844", ["&:hover"] : ({ ["background"] : "#818cf828" }), ["&:focus-visible"] : ({ ["outline"] : "2px solid #818cf8", ["outlineOffset"] : "2px" }) }),onClick:on_click_3afd465f89ffb4133e30b4f20295ae5a,role:"button",tabIndex:0},children)
    )
});
