
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_a8b5159902e8710bb1fda4e63fc67f64 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_5a1eb0343590d6915ba5b22f68c41852 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.open_sheet", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["fontSize"] : "11px", ["letterSpacing"] : "0.08em", ["padding"] : "8px 12px", ["borderRadius"] : "8px", ["background"] : "#BF5AF2", ["color"] : "#fff", ["cursor"] : "pointer", ["whiteSpace"] : "nowrap", ["flexShrink"] : "0", ["&:hover"] : ({ ["opacity"] : "0.9" }) }),onClick:on_click_5a1eb0343590d6915ba5b22f68c41852},children)
    )
});
