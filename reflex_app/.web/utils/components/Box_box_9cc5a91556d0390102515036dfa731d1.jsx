
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_9cc5a91556d0390102515036dfa731d1 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_3afd465f89ffb4133e30b4f20295ae5a = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_panel", ({ ["name"] : "setup" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["marginTop"] : "12px", ["padding"] : "8px 20px", ["borderRadius"] : "8px", ["cursor"] : "pointer", ["fontSize"] : "13px", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["background"] : "#BF5AF218", ["color"] : "#BF5AF2", ["border"] : "1px solid #BF5AF244", ["&:hover"] : ({ ["background"] : "#BF5AF228" }), ["&:focus-visible"] : ({ ["outline"] : "2px solid #BF5AF2", ["outlineOffset"] : "2px" }) }),onClick:on_click_3afd465f89ffb4133e30b4f20295ae5a,role:"button",tabIndex:0},children)
    )
});
